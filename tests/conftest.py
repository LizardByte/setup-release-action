# standard imports
import os
import shutil

# lib imports
from dotenv import load_dotenv
import pytest
import requests

# set environment variables
load_dotenv()
os.environ['GITHUB_REPOSITORY'] = 'LizardByte/setup-release-action'
os.environ['GITHUB_OUTPUT'] = 'github_output.md'
os.environ['GITHUB_STEP_SUMMARY'] = 'github_step_summary.md'
os.environ['GITHUB_WORKSPACE'] = os.path.join(os.getcwd(), 'github', 'workspace')
os.environ['INPUT_CHANGELOG_PATH'] = 'CHANGELOG.md'
os.environ['INPUT_EVENT_API_MAX_ATTEMPTS'] = '1'
os.environ['INPUT_FAIL_ON_EVENTS_API_ERROR'] = 'false'

try:
    GITHUB_TOKEN = os.environ['INPUT_GITHUB_TOKEN']
except KeyError:
    os.environ['INPUT_GITHUB_TOKEN'] = ''
    GITHUB_TOKEN = os.environ['INPUT_GITHUB_TOKEN']

GITHUB_HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}

# globals
COMMIT = None


def pytest_runtest_setup(item):
    if 'github_token' in item.fixturenames and not GITHUB_TOKEN:
        pytest.skip('INPUT_GITHUB_TOKEN environment variable not set')


@pytest.fixture(scope='session')
def github_token():
    yield


@pytest.fixture(scope='function')
def github_output_file():
    f = os.environ['GITHUB_OUTPUT']

    # touch the file
    with open(f, 'w') as fi:
        fi.write('')

    yield f

    # re-touch the file
    with open(f, 'w') as fi:
        fi.write('')


@pytest.fixture(scope='function')
def github_step_summary_file():
    f = os.environ['GITHUB_STEP_SUMMARY']

    # touch the file
    with open(f, 'w') as fi:
        fi.write('')

    yield f

    # re-touch the file
    with open(f, 'w') as fi:
        fi.write('')


@pytest.fixture(scope='function', params=[0, 1, 2])
def changelog_set(request):
    change_set = request.param

    # get set directory
    set_dir = os.path.join(os.getcwd(), 'tests', 'data', f'set{change_set}')

    # workspace directory
    workspace_dir = os.path.join(os.getcwd(), 'github', 'workspace')

    # copy the changelog to `github/workspace`
    os.makedirs(workspace_dir, exist_ok=True)
    try:
        shutil.copyfile(
            src=os.path.join(set_dir, 'CHANGELOG.md'),
            dst=os.path.join(workspace_dir, 'CHANGELOG.md')
        )
    except FileNotFoundError:
        pass  # set0 does not have a CHANGELOG.md file

    # read the version from the version.txt file
    with open(os.path.join(set_dir, 'version.txt'), 'r') as f:
        version = f.read().strip()

    # read the date from the date.txt file
    with open(os.path.join(set_dir, 'date.txt'), 'r') as f:
        date = f.read().strip()

    # read the url from the url.txt file
    with open(os.path.join(set_dir, 'url.txt'), 'r') as f:
        url = f.read().strip()

    # read the changes from the changes.txt file
    with open(os.path.join(set_dir, 'changes.txt'), 'r') as f:
        changes = f.read().strip()

    fixture = dict(
        changelog_expected=True if change_set > 0 else False,
        changelog_path=os.path.join(workspace_dir, 'CHANGELOG.md'),
        version=version,
        date=date,
        url=url,
        changes=changes,
    )

    yield fixture

    # clean the workspace
    shutil.rmtree(workspace_dir)


@pytest.fixture(scope='function')
def latest_commit(github_token):
    global COMMIT
    original_sha = os.environ.get('GITHUB_SHA', '')

    if not COMMIT:
        # get commits on the default branch
        github_api_url = f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/commits"
        response = requests.get(
            url=github_api_url,
            headers=GITHUB_HEADERS,
            params={'sha': 'master'},
        )
        data = response.json()
        COMMIT = data[0]['sha']

    os.environ['GITHUB_SHA'] = COMMIT
    yield COMMIT

    os.environ['GITHUB_SHA'] = original_sha


@pytest.fixture(scope='function')
def dummy_commit():
    original_sha = os.environ.get('GITHUB_SHA', '')
    os.environ['GITHUB_SHA'] = 'not-a-real-commit'
    yield

    os.environ['GITHUB_SHA'] = original_sha


@pytest.fixture(scope='function', params=[True, False])
def github_event_path(request):
    # true is original file from GitHub context
    # false is dummy file

    original_value = os.environ['GITHUB_EVENT_PATH']
    if request.param:
        yield
    else:
        os.environ['GITHUB_EVENT_PATH'] = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'dummy_github_event.json'
        )
        yield
        os.environ['GITHUB_EVENT_PATH'] = original_value


@pytest.fixture(scope='function')
def dummy_github_event_path():
    original_value = os.environ['GITHUB_EVENT_PATH']
    os.environ['GITHUB_EVENT_PATH'] = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'dummy_github_event.json'
    )
    yield
    os.environ['GITHUB_EVENT_PATH'] = original_value


@pytest.fixture(scope='function')
def fail_on_events_api_error():
    os.environ['INPUT_FAIL_ON_EVENTS_API_ERROR'] = 'true'
    yield
    os.environ['INPUT_FAIL_ON_EVENTS_API_ERROR'] = 'false'


@pytest.fixture(params=[True, False], scope='function')
def input_dotnet(request):
    os.environ['INPUT_DOTNET'] = str(request.param).lower()
    yield

    del os.environ['INPUT_DOTNET']
