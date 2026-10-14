import hashlib
import subprocess
import sys
import textwrap

from opensmtpd_filters.filter_engine import FilterEngine


def _build_multipart_message_lines() -> list[str]:
    """ Return a realistic multipart email as a list of lines. """
    
    return [
        "From: sender@example.com",
        "To: recipient@example.com",
        "Subject: Test multipart message",
        "MIME-Version: 1.0",
        'Content-Type: multipart/mixed; boundary="boundary123"',
        "",
        "--boundary123",
        'Content-Type: text/plain; charset="utf-8"',
        "",
        "Hello, this is the text part of the email.",
        "",
        "--boundary123",
        "Content-Type: application/octet-stream",
        'Content-Disposition: attachment; filename="data.bin"',
        "",
        "Binary content placeholder",
        "",
        "--boundary123--",
    ]


def _compute_hash(lines: list[str]) -> str:
    """ Compute an SHA-256 hex digest over the joined message lines. """
    
    content = "\n".join(lines)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _build_protocol_lines(session_id: str, token: str, message_lines: list[str]) -> list[str]:
    """
    Build the full set of protocol lines that simulate an OpenSMTPd filter session.
    
    Returns a list of lines:
     #. Config handshake lines ending with ``config|ready``,
     #. link-connect report,
     #. data-line filter events for each message line (dot-stuffed),
     #. end-of-data marker (``.``),
     #. commit filter event.
    """
    
    lines: list[str] = [
        # Config handshake
        "config|smtpd-version|OpenSMTPD",
        "config|smtp-session-timeout|600",
        "config|subsystem|smtp-in",
        FilterEngine.CONFIGURATION_READY,
        # link-connect report
        f"report|0.7|1577836800.000010|smtp-in|link-connect|{session_id}|localhost|pass|127.0.0.1:1234|127.0.0.1:25"
    ]
    
    # data-line filter events for each message line
    for line in message_lines:
        # In the real protocol, lines starting with '.' are dot-stuffed to '..'
        stuffed = ".." + line if line.startswith(".") else line
        lines.append(f"filter|0.7|1577836800.100000|smtp-in|data-line|{session_id}|{token}|{stuffed}")
    
    # End-of-data marker
    lines.append(f"filter|0.7|1577836800.200000|smtp-in|data-line|{session_id}|{token}|.")
    
    # commit filter event
    lines.append(f"filter|0.7|1577836800.300000|smtp-in|commit|{session_id}|{token}")
    
    return lines


class TestMessageBodyFilterIntegration:
    """
    Integration tests that run the actual ``filter_loop()`` via subprocess with real pipe-based I/O — no mocking of
    internal engine methods.
    """
    
    def test_when_email_filtered_then_hash_header_added(self) -> None:
        """
        Verify that when a multipart email is processed via ``register_message_body_filter``, the message body filter
        callback receives the full set of message lines, computes an SHA-256 hash, and injects the ``X-HASH`` header
        into the returned lines.
        
        The test spawns a subprocess that creates a FilterEngine instance, registers the message body filter,
        and runs filter_loop(). Protocol messages are fed through stdin, and responses are captured from stdout.
        """
        
        session_id = "82a3bd08e3a8db65"
        token = "82a3bd08e3a8db66"
        message_lines = _build_multipart_message_lines()
        expected_hash = _compute_hash(message_lines)
        
        # Build the Python script that runs the filter engine.
        # filter_loop() runs forever; when stdin is exhausted it raises FilterEngineException. It is caught so the
        # subprocess exits cleanly.
        filter_script = textwrap.dedent('''\
            import sys
            import hashlib
            from opensmtpd_filters.filter_engine import FilterEngine, FilterEngineException, SessionContext
            
            def _compute_hash(lines):
                content = "\\n".join(lines)
                return hashlib.sha256(content.encode("utf-8")).hexdigest()
            
            def _message_processor(session_ctx: SessionContext, lines: list) -> list:
                """ Compute hash and prepend X-HASH header. """
                
                computed_hash = _compute_hash(lines)
                return ["X-HASH: " + computed_hash] + lines
            
            def main():
                engine = FilterEngine()
                engine.register_message_body_filter(_message_processor)
                try:
                    engine.filter_loop()
                except FilterEngineException:
                    # stdin exhausted — expected in tests
                    pass
            
            if __name__ == "__main__":
                main()
        ''')
        # Build protocol input lines
        protocol_lines = _build_protocol_lines(session_id, token, message_lines)
        
        # Run the filter engine in a subprocess with pipes for stdin/stdout
        result = subprocess.run(
            [sys.executable, "-c", filter_script],
            input="\n".join(protocol_lines) + "\n",
            capture_output=True,
            text=True,
            timeout=10
        )
        # The subprocess should complete successfully
        assert result.returncode == 0, f"Filter engine stderr: {result.stderr}"
        
        # Parse the output lines from the filter engine
        output_lines = result.stdout.strip().split("\n")

        # 1. The engine should send register|ready after config handshake
        assert FilterEngine.ANSWER_REGISTER_READY in output_lines, \
            f"Expected 'register|ready' in output. Got: {output_lines}"
        
        # 2. The engine should register the processors it needs
        #    (link-connect, link-disconnect, data-line, commit)
        register_lines = [l for l in output_lines if l.startswith("register|")]
        assert any("link-connect" in l for l in register_lines), "Expected link-connect registration"
        assert any("data-line" in l for l in register_lines), "Expected data-line registration"
        assert any("commit" in l for l in register_lines), "Expected commit registration"
        
        # 3. Extract filter-dataline responses (the filtered message output)
        #    Format: filter-dataline|session_id|token|payload  (protocol >= 0.5)
        dataline_payloads: list[str] = []
        for line in output_lines:
            if line.startswith("filter-dataline|"):
                parts = line.split("|")
                if len(parts) >= 4:
                    payload = parts[3]
                    if payload != ".":
                        dataline_payloads.append(payload)
        
        # The first data-line should be the X-HASH header
        assert len(dataline_payloads) > 0, f"No filter-dataline responses found. Output: {output_lines}"
        assert dataline_payloads[0] == f"X-HASH: {expected_hash}", (f"Expected first line to be 'X-HASH: "
                                                                    "{expected_hash}', got '{dataline_payloads[0]}'")
        
        # The second line should be the first original message line
        assert dataline_payloads[1] == message_lines[0], (f"Expected second line to be '{message_lines[0]}', "
                                                          f"got '{dataline_payloads[1]}'")
        
        # Total data lines = 1 (X-HASH) + len(message_lines)
        assert len(dataline_payloads) == 1 + len(message_lines), (f"Expected {1 + len(message_lines)} data lines, "
                                                                  f"got {len(dataline_payloads)}")
        
        # 4. Verify all original message lines are preserved in order
        for i, original_line in enumerate(message_lines):
            assert dataline_payloads[i + 1] == original_line, (f"Line {i} mismatch: expected '{original_line}', "
                                                               f"got '{dataline_payloads[i + 1]}'")
        
        # 5. The commit response should be "proceed"
        filter_result_lines = [l for l in output_lines if l.startswith("filter-result|")]
        assert len(filter_result_lines) >= 1, f"No filter-result responses found. Output: {output_lines}"
        assert "proceed" in filter_result_lines[-1], (f"Expected 'proceed' in commit response, "
                                                      f"got '{filter_result_lines[-1]}'")
    
    def test_message_body_filter_handles_dot_stuffing(self) -> None:
        """
        Verify that the message body filter correctly handles dot-stuffed lines (lines starting with '.' are escaped
        to '..' in SMTP protocol).
        
        The test feeds dot-stuffed lines through the protocol and verifies the filter engine passes the un-escaped
        content to the callback.
        """
        
        session_id = "abc123"
        token = "def456"
        
        # Original message lines (what the user callback should see)
        message_lines = [
            "From: test@example.com",
            ".hidden line",
            "Normal line"
        ]
        
        # Dot-stuffed lines as sent over the SMTP protocol
        # Only the second line should be dot-stuffed
        stuffed_lines = [
            "From: test@example.com",
            "..hidden line",
            "Normal line"
        ]
        
        # Build a script that echoes back the received lines so we can verify the un-escaping worked correctly
        filter_script = textwrap.dedent('''\
            import sys
            from opensmtpd_filters.filter_engine import FilterEngine, FilterEngineException, SessionContext
            
            def _message_processor(session_ctx: SessionContext, lines: list) -> list:
                # Echo back the lines prefixed with "ECHO: " to verify un-escaping
                return ["ECHO: " + line for line in lines]
            
            def main():
                engine = FilterEngine()
                engine.register_message_body_filter(_message_processor)
                try:
                    engine.filter_loop()
                except FilterEngineException:
                    # stdin exhausted — expected in tests
                    pass
            
            if __name__ == "__main__":
                main()
        ''')
        
        # Build protocol lines with dot-stuffed content
        protocol_lines: list[str] = [
            FilterEngine.CONFIGURATION_READY,
            f"report|0.7|1577836800.000010|smtp-in|link-connect|{session_id}|localhost|pass|127.0.0.1:1234|127.0.0.1:25"
        ]
        for line in stuffed_lines:
            protocol_lines.append(f"filter|0.7|1577836800.100000|smtp-in|data-line|{session_id}|{token}|{line}")
        protocol_lines.append(f"filter|0.7|1577836800.200000|smtp-in|data-line|{session_id}|{token}|.")
        protocol_lines.append(f"filter|0.7|1577836800.300000|smtp-in|commit|{session_id}|{token}")
        
        result = subprocess.run(
            [sys.executable, "-c", filter_script],
            input="\n".join(protocol_lines) + "\n",
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        assert result.returncode == 0, f"Filter engine stderr: {result.stderr}"
        
        output_lines = result.stdout.strip().split("\n")
        # Extract filter-dataline payloads
        dataline_payloads: list[str] = []
        for line in output_lines:
            if line.startswith("filter-dataline|"):
                parts = line.split("|")
                if len(parts) >= 4:
                    payload = parts[3]
                    if payload != ".":
                        dataline_payloads.append(payload)
        
        # The processor should receive the un-escaped (original) lines
        # and echo them back with "ECHO: " prefix
        expected_echoes = ["ECHO: " + line for line in message_lines]
        assert dataline_payloads == expected_echoes, f"Expected {expected_echoes}, got {dataline_payloads}"
    
    def test_session_context_tracks_link_connect_and_disconnect(self) -> None:
        """
        Verify that ``track_session_context`` properly creates a SessionContext on link-connect and removes it on
        link-disconnect.
        
        The test sends link-connect and link-disconnect report events and verifies the engine processes them without
        error.
        """
        
        session_id = "sess-001"
        
        filter_script = textwrap.dedent('''\
            import sys
            from opensmtpd_filters.filter_engine import FilterEngine, FilterEngineException
            
            def main():
                engine = FilterEngine()
                engine.track_session_context()
                try:
                    engine.filter_loop()
                except FilterEngineException:
                    # stdin exhausted — expected in tests
                    pass
            
            if __name__ == "__main__":
                main()
        ''')
        
        protocol_lines = [
            FilterEngine.CONFIGURATION_READY,
            f"report|0.7|1577836800.000010|smtp-in|link-connect|{session_id}"
            f"|mail.example.com|pass|192.168.1.1:54321|10.0.0.1:25",
            f"report|0.7|1577836800.100000|smtp-in|link-disconnect|{session_id}",
        ]
        
        result = subprocess.run(
            [sys.executable, "-c", filter_script],
            input="\n".join(protocol_lines) + "\n",
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        # The engine should process the events without error
        assert result.returncode == 0, f"Filter engine stderr: {result.stderr}"
        
        output_lines = result.stdout.strip().split("\n")
        # The engine should register link-connect and link-disconnect handlers
        register_lines = [l for l in output_lines if l.startswith("register|")]
        assert any("link-connect" in l for l in register_lines), "Expected link-connect registration"
        assert any("link-disconnect" in l for l in register_lines), "Expected link-disconnect registration"
