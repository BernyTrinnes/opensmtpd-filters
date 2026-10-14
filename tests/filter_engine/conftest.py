from typing import Generator
from unittest.mock import Mock

import pytest
from pytest import Config
from pytest_mock import MockerFixture

from opensmtpd_filters.filter_engine import FilterEngine


@pytest.fixture(scope="class", autouse=True)
def suspend_capture(pytestconfig: Config, request) -> None:
    """ Automatically applied Pytest fixture to suppress the stdout/sdtin capture during the tests. """
    
    
    class SuspendGuard:
        def __init__(self):
            self.capture_manager = pytestconfig.pluginmanager.getplugin('capturemanager')
        
        def __enter__(self):
            self.capture_manager.suspend_global_capture(in_=True)
        
        def __exit__(self, _1, _2, _3):
            self.capture_manager.resume_global_capture()
    
    
    request.cls.suspend_capture = SuspendGuard()


@pytest.fixture
def mocked_channel_in(mocker: MockerFixture) -> Generator[Mock, None, None]:
    """ Pytest fixture to mock the input channel in the OpenSMTPd filter engine. """
    
    _mocked_channel_in = mocker.patch("opensmtpd_filters.filter_engine.engine.open_in", new_callable=mocker.mock_open)
    yield _mocked_channel_in
    mocker.stop(_mocked_channel_in)


@pytest.fixture
def mocked_channel_out(mocker: MockerFixture) -> Generator[Mock, None, None]:
    """ Pytest fixture to mock the output channel in the OpenSMTPd filter engine. """
    
    _mocked_channel_out = mocker.patch("opensmtpd_filters.filter_engine.engine.open_out", new_callable=mocker.mock_open)
    yield _mocked_channel_out
    mocker.stop(_mocked_channel_out)


@pytest.fixture
def mocked_channel_err(mocker: MockerFixture) -> Generator[Mock, None, None]:
    _mocked_channel_err = mocker.patch("opensmtpd_filters.filter_engine.engine.open_err", new_callable=mocker.mock_open)
    yield _mocked_channel_err
    mocker.stop(_mocked_channel_err)


@pytest.fixture(autouse=True)
def mock_communication_channels(mocked_channel_in: Mock, mocked_channel_out: Mock, mocked_channel_err: Mock,
        request) -> None:
    """ Automatically applied Pytest fixture to mock the input/output/error channels in the OpenSMTPd filter engine. """
    
    request.cls.channel_in = mocked_channel_in
    request.cls.channel_out = mocked_channel_out
    request.cls.channel_err = mocked_channel_err

@pytest.fixture
def mocked_filter_stream_filter(mocker: MockerFixture) -> Generator[Mock, None, None]:
    """ Pytest fixture to mock the method ``_filter_stream_filter`` from the class ``FilterEngine``. """
    
    _mocked_filter_stream_filter = mocker.patch.object(FilterEngine, "_filter_stream_filter")
    yield _mocked_filter_stream_filter
    mocker.stop(_mocked_filter_stream_filter)


@pytest.fixture
def mocked_filter_stream_report(mocker: MockerFixture) -> Generator[Mock, None, None]:
    """ Pytest fixture to mock the method ``_filter_stream_report`` from the class ``FilterEngine``. """
    
    _mocked_filter_stream_report = mocker.patch.object(FilterEngine, "_filter_stream_report")
    yield _mocked_filter_stream_report
    mocker.stop(_mocked_filter_stream_report)
