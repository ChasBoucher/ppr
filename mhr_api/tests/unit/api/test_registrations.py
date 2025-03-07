# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests to verify the endpoints for maintaining MH registrations.

Test-Suite to ensure that the /registrations endpoint is working as expected.
"""
import copy
from http import HTTPStatus

import pytest
from flask import current_app
from registry_schemas.example_data.mhr import REGISTRATION

from mhr_api.models import MhrRegistration, registration_utils as reg_utils
from mhr_api.services.authz import COLIN_ROLE, MHR_ROLE, STAFF_ROLE, BCOL_HELP, ASSETS_HELP
from tests.unit.services.utils import create_header, create_header_account


MOCK_AUTH_URL = 'https://bcregistry-bcregistry-mock.apigee.net/mockTarget/auth/api/v1/'
MOCK_PAY_URL = 'https://bcregistry-bcregistry-mock.apigee.net/mockTarget/pay/api/v1/'

# testdata pattern is ({desc}, {roles}, {status}, {has_account}, {results_size})
TEST_GET_ACCOUNT_DATA = [
    ('Missing account', [MHR_ROLE], HTTPStatus.BAD_REQUEST, False, 0),
    ('Invalid role', [COLIN_ROLE], HTTPStatus.UNAUTHORIZED, True, 0),
    ('Valid request', [MHR_ROLE], HTTPStatus.OK, True, 1),
    ('Invalid request staff no account', [MHR_ROLE, STAFF_ROLE], HTTPStatus.BAD_REQUEST, False, 0)
]
# testdata pattern is ({description}, {has_submitting}, {roles}, {status}, {has_account})
TEST_CREATE_DATA = [
    ('Invalid schema validation no submitting', False, [MHR_ROLE, STAFF_ROLE], HTTPStatus.BAD_REQUEST, True),
    ('Missing account', True, [MHR_ROLE], HTTPStatus.BAD_REQUEST, False),
    ('Staff missing account', True, [MHR_ROLE, STAFF_ROLE], HTTPStatus.BAD_REQUEST, False),
    ('Invalid role', True, [COLIN_ROLE], HTTPStatus.UNAUTHORIZED, True),
    ('Invalid non-staff role', True, [MHR_ROLE], HTTPStatus.UNAUTHORIZED, True),
    ('Valid staff', True, [MHR_ROLE, STAFF_ROLE], HTTPStatus.CREATED, True)
]
# testdata pattern is ({description}, {roles}, {status}, {account}, {mhr_num})
TEST_GET_REGISTRATION = [
    ('Missing account', [MHR_ROLE], HTTPStatus.BAD_REQUEST, None, '150062'),
    ('Invalid role', [COLIN_ROLE], HTTPStatus.UNAUTHORIZED, '2523', '150062'),
    ('Valid Request', [MHR_ROLE], HTTPStatus.OK, '2523', '150062'),
    ('Valid Request reg staff', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, STAFF_ROLE, '150062'),
    ('Valid Request bcol helpdesk', [MHR_ROLE, BCOL_HELP], HTTPStatus.OK, ASSETS_HELP, '150062'),
    ('Valid Request other account', [MHR_ROLE], HTTPStatus.OK, 'PS12345', '150062'),
    ('Invalid MHR Number', [MHR_ROLE], HTTPStatus.NOT_FOUND, '2523', 'TESTXXXX'),
    ('Invalid request Staff no account', [MHR_ROLE, STAFF_ROLE], HTTPStatus.BAD_REQUEST, None, '150062')
]
# testdata pattern is ({desc}, {roles}, {status}, {sort_criteria}, {sort_direction})
TEST_GET_ACCOUNT_DATA_SORT2 = [
    ('Sort mhr number', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.MHR_NUMBER_PARAM, None)
]
TEST_GET_ACCOUNT_DATA_SORT = [
    ('Sort mhr number', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.MHR_NUMBER_PARAM, None),
    ('Sort reg type asc', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.REG_TYPE_PARAM, reg_utils.SORT_ASCENDING),
    ('Sort reg status desc', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.STATUS_PARAM, reg_utils.SORT_DESCENDING),
    ('Sort reg ts asc', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.REG_TS_PARAM, reg_utils.SORT_ASCENDING),
    ('Sort client ref', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.CLIENT_REF_PARAM, None),
    ('Sort user name', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.USER_NAME_PARAM, None),
    ('Sort submitting name', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.SUBMITTING_NAME_PARAM, None),
    ('Sort owner name', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.OWNER_NAME_PARAM, None)
]
# testdata pattern is ({desc}, {roles}, {status}, {filter_name}, {filter_value})
TEST_GET_ACCOUNT_DATA_FILTER = [
    ('Filter mhr number', '2523', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.MHR_NUMBER_PARAM, '098487'),
    ('Filter reg type', '2523', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.REG_TYPE_PARAM, 'REGISTER NEW UNIT'),
    ('Filter reg status', '2523', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.STATUS_PARAM, 'ACTIVE'),
    ('Filter client ref', '2523', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.CLIENT_REF_PARAM, 'a000873'),
    ('Filter user name', '2523', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.USER_NAME_PARAM, 'BCREG2'),
    ('Filter submitting bus name', '2523', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.SUBMITTING_NAME_PARAM,
     'champion'),
    ('Filter submitting last name', '2523', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.SUBMITTING_NAME_PARAM,
     'iverson'),
    ('Filter submitting first name', '2523', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, reg_utils.SUBMITTING_NAME_PARAM,
     'donna')
]
# testdata pattern is ({desc}, {roles}, {status}, {collapse}, {filter_start}, {filter_end})
TEST_GET_ACCOUNT_DATA_FILTER_DATE = [
    ('Filter reg date range', '2523', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, False,
     '2021-10-14T09:53:57-07:53', '2021-10-17T09:53:57-07:53'),
    ('Filter reg date range', '2523', [MHR_ROLE, STAFF_ROLE], HTTPStatus.OK, True,
     '2021-10-14T09:53:57-07:53', '2021-10-17T09:53:57-07:53')
]


@pytest.mark.parametrize('desc,roles,status,has_account,results_size', TEST_GET_ACCOUNT_DATA)
def test_get_account_registrations(session, client, jwt, desc, roles, status, has_account, results_size):
    """Assert that a get account registrations summary list endpoint works as expected."""
    headers = None
    # setup
    if has_account:
        headers = create_header_account(jwt, roles)
    else:
        headers = create_header(jwt, roles)
    # test
    rv = client.get('/api/v1/registrations',
                    headers=headers)

    # check
    # print(rv.json)
    assert rv.status_code == status
    if rv.status_code == HTTPStatus.OK:
        assert rv.json
        assert len(rv.json) >= results_size
        for registration in rv.json:
            assert registration['mhrNumber']
            assert registration['registrationDescription']
            assert registration['statusType'] is not None
            assert registration['createDateTime'] is not None
            assert registration['username'] is not None
            assert registration['submittingParty'] is not None
            assert registration['clientReferenceId'] is not None
            assert registration['ownerNames'] is not None
            assert registration['path'] is not None
            if registration['registrationDescription'] == 'REGISTER NEW UNIT':
                assert 'lienRegistrationType' in registration


@pytest.mark.parametrize('desc,has_submitting,roles,status,has_account', TEST_CREATE_DATA)
def test_create(session, client, jwt, desc, has_submitting, roles, status, has_account):
    """Assert that a post MH registration works as expected."""
    # setup
    current_app.config.update(PAYMENT_SVC_URL=MOCK_PAY_URL)
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    json_data = copy.deepcopy(REGISTRATION)
    if not has_submitting:
        del json_data['submittingParty']
    if has_account:
        headers = create_header_account(jwt, roles)
    else:
        headers = create_header(jwt, roles)
    if status == HTTPStatus.CREATED and STAFF_ROLE in roles:
        json_data['documentId'] = '80048756'

    # test
    response = client.post('/api/v1/registrations',
                           json=json_data,
                           headers=headers,
                           content_type='application/json')

    # check
    assert response.status_code == status
    if response.status_code == HTTPStatus.CREATED:
        registration: MhrRegistration = MhrRegistration.find_by_mhr_number(response.json['mhrNumber'],
                                                                           'PS12345')
        assert registration


@pytest.mark.parametrize('desc,roles,status,account_id,mhr_num', TEST_GET_REGISTRATION)
def test_get_registration(session, client, jwt, desc, roles, status, account_id, mhr_num):
    """Assert that a get account registration by MHR number works as expected."""
    # setup
    current_app.config.update(AUTH_SVC_URL=MOCK_AUTH_URL)
    headers = None
    if account_id:
        headers = create_header_account(jwt, roles, 'test-user', account_id)
    else:
        headers = create_header(jwt, roles)

    # test
    response = client.get('/api/v1/registrations/' + mhr_num,
                          headers=headers)
    # check
    if status == HTTPStatus.NOT_FOUND:
        assert response.status_code in (status, HTTPStatus.UNAUTHORIZED)
    else:
        assert response.status_code == status


@pytest.mark.parametrize('desc,roles,status,sort_criteria,sort_direction', TEST_GET_ACCOUNT_DATA_SORT)
def test_get_account_registrations_sort(session, client, jwt, desc, roles, status, sort_criteria, sort_direction):
    """Assert that a get account registrations summary list endpoint with sorting works as expected."""
    headers = None
    # setup
    headers = create_header_account(jwt, roles)
    params = f'?sortCriteriaName={sort_criteria}'
    if sort_direction:
        params += f'&sortDirection={sort_direction}'
    # test
    current_app.logger.debug('params=' + params)
    rv = client.get('/api/v1/registrations' + params,
                    headers=headers)
    # check
    assert rv.status_code == status
    assert rv.json
    for registration in rv.json:
        assert registration['mhrNumber']
        assert registration['registrationDescription']
        assert registration['statusType'] is not None
        assert registration['createDateTime'] is not None
        assert registration['username'] is not None
        assert registration['submittingParty'] is not None
        assert registration['clientReferenceId'] is not None
        assert registration['ownerNames'] is not None
        assert registration['path'] is not None


@pytest.mark.parametrize('desc,account_id,roles,status,filter_name,filter_value', TEST_GET_ACCOUNT_DATA_FILTER)
def test_get_account_registrations_filter(session, client, jwt, desc, account_id, roles, status, filter_name,
                                          filter_value):
    """Assert that a get account registrations summary list endpoint with filtering works as expected."""
    # setup
    headers = create_header_account(jwt, roles, 'test-user', account_id)
    params = f'?{filter_name}={filter_value}'
    # test
    rv = client.get('/api/v1/registrations' + params,
                    headers=headers)
    # check
    assert rv.status_code == status
    assert rv.json
    for registration in rv.json:
        assert registration['mhrNumber']
        assert registration['registrationDescription']
        assert registration['statusType'] is not None
        assert registration['createDateTime'] is not None
        assert registration['username'] is not None
        assert registration['submittingParty'] is not None
        assert registration['clientReferenceId'] is not None
        assert registration['ownerNames'] is not None
        assert registration['path'] is not None


@pytest.mark.parametrize('desc,account_id,roles,status,collapse,filter_start,filter_end',
                         TEST_GET_ACCOUNT_DATA_FILTER_DATE)
def test_get_account_registrations_filter_date(session, client, jwt, desc, account_id, roles, status, collapse,
                                               filter_start, filter_end):
    """Assert that a get account registrations summary list endpoint with filtering works as expected."""
    # setup
    headers = create_header_account(jwt, roles, 'test-user', account_id)
    start_ts: str = reg_utils.START_TS_PARAM
    end_ts: str = reg_utils.END_TS_PARAM
    params = f'?{start_ts}={filter_start}&{end_ts}={filter_end}'
    if collapse:
        params += '&collapse=true'
    # test
    rv = client.get('/api/v1/registrations' + params,
                    headers=headers)
    # check
    assert rv.status_code == status
    assert rv.json
    for registration in rv.json:
        assert registration['mhrNumber']
        assert registration['registrationDescription']
        assert registration['statusType'] is not None
        assert registration['createDateTime'] is not None
        assert registration['username'] is not None
        assert registration['submittingParty'] is not None
        assert registration['clientReferenceId'] is not None
        assert registration['ownerNames'] is not None
        assert registration['path'] is not None
