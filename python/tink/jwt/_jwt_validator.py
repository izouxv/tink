# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
"""The JwtValidator."""

import datetime

from typing import Optional
from tink.jwt import _jwt_error
from tink.jwt import _raw_jwt

_MAX_CLOCK_SKEW = datetime.timedelta(minutes=10)


class JwtValidator:
  """A JwtValidator defines how JSON Web Tokens (JWTs) should be validated.

    By default, the JwtValidator requires that a token has a valid expiration
    claim, no issuer and no audience claim. This can be changed using the
    expect_... and  ignore_... arguments.

    If present, the JwtValidator also validates the not-before claim. The
    validation time can be changed using the fixed_now parameter. clock_skew can
    be set to allow a small leeway (not more than 10 minutes) to account for
    clock skew.
  """

  def __init__(self,
               *,
               expected_type_header: Optional[str],
               expected_issuer: Optional[str],
               expected_audience: Optional[str],
               ignore_type_header: bool,
               ignore_issuer: bool,
               ignore_audiences: bool,
               allow_missing_expiration: bool,
               expect_issued_in_the_past: bool,
               clock_skew: Optional[datetime.timedelta],
               fixed_now: Optional[datetime.datetime]) -> None:
    if expected_type_header and ignore_type_header:
      raise ValueError(
          'expected_type_header and ignore_type_header cannot be used together')
    if expected_issuer and ignore_issuer:
      raise ValueError(
          'expected_issuer and ignore_issuer cannot be used together')
    if expected_audience and ignore_audiences:
      raise ValueError(
          'expected_audience and ignore_audiences cannot be used together')
    self._expected_type_header = expected_type_header
    self._expected_issuer = expected_issuer
    self._expected_audience = expected_audience
    self._ignore_type_header = ignore_type_header
    self._ignore_issuer = ignore_issuer
    self._ignore_audiences = ignore_audiences
    self._allow_missing_expiration = allow_missing_expiration
    self._expect_issued_in_the_past = expect_issued_in_the_past
    if clock_skew:
      if clock_skew > _MAX_CLOCK_SKEW:
        raise ValueError('clock skew too large, max is 10 minutes')
      self._clock_skew = clock_skew
    else:
      self._clock_skew = datetime.timedelta()
    if fixed_now and not fixed_now.tzinfo:
      raise ValueError('fixed_now without tzinfo')
    self._fixed_now = fixed_now

  def has_expected_type_header(self) -> bool:
    return self._expected_type_header is not None

  def expected_type_header(self) -> Optional[str]:
    return self._expected_type_header

  def has_expected_issuer(self) -> bool:
    return self._expected_issuer is not None

  def expected_issuer(self) -> Optional[str]:
    return self._expected_issuer

  def has_expected_audience(self) -> bool:
    return self._expected_audience is not None

  def expected_audience(self) -> Optional[str]:
    return self._expected_audience

  def ignore_type_header(self) -> bool:
    return self._ignore_type_header

  def ignore_issuer(self) -> bool:
    return self._ignore_issuer

  def ignore_audiences(self) -> bool:
    return self._ignore_audiences

  def allow_missing_expiration(self) -> bool:
    return self._allow_missing_expiration

  def expect_issued_in_the_past(self) -> bool:
    return self._expect_issued_in_the_past

  def clock_skew(self) -> datetime.timedelta:
    return self._clock_skew

  def has_fixed_now(self) -> bool:
    return self._fixed_now is not None

  def fixed_now(self) -> Optional[datetime.datetime]:
    return self._fixed_now


def new_validator(
    *,
    expected_type_header: Optional[str] = None,
    expected_issuer: Optional[str] = None,
    expected_audience: Optional[str] = None,
    ignore_type_header: bool = False,
    ignore_issuer: bool = False,
    ignore_audiences: bool = False,
    allow_missing_expiration: bool = False,
    expect_issued_in_the_past: bool = False,
    clock_skew: Optional[datetime.timedelta] = None,
    fixed_now: Optional[datetime.datetime] = None) -> JwtValidator:
  """Creates a new JwtValidator."""
  return JwtValidator(
      expected_type_header=expected_type_header,
      expected_issuer=expected_issuer,
      expected_audience=expected_audience,
      ignore_type_header=ignore_type_header,
      ignore_issuer=ignore_issuer,
      ignore_audiences=ignore_audiences,
      allow_missing_expiration=allow_missing_expiration,
      expect_issued_in_the_past=expect_issued_in_the_past,
      clock_skew=clock_skew,
      fixed_now=fixed_now)


def validate(validator: JwtValidator, raw_jwt: _raw_jwt.RawJwt) -> None:
  """Validates a jwt.RawJwt and raises JwtInvalidError if it is invalid.

  This function is called by the JWT primitives and does not need to be called
  by the user.

  Args:
    validator: a jwt.JwtValidator that defines how to validate tokens.
    raw_jwt: a jwt.RawJwt token to validate.
  Raises:
    jwt.JwtInvalidError
  """
  if validator.has_fixed_now():
    now = validator.fixed_now()
  else:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
  if not raw_jwt.has_expiration() and not validator.allow_missing_expiration():
    raise _jwt_error.JwtInvalidError('token is missing an expiration')
  if (raw_jwt.has_expiration() and
      raw_jwt.expiration() <= now - validator.clock_skew()):
    raise _jwt_error.JwtInvalidError('token has expired since %s' %
                                     raw_jwt.expiration())
  if (raw_jwt.has_not_before() and
      raw_jwt.not_before() > now + validator.clock_skew()):
    raise _jwt_error.JwtInvalidError('token cannot be used before %s' %
                                     raw_jwt.not_before())
  if validator.expect_issued_in_the_past():
    if not raw_jwt.has_issued_at():
      raise _jwt_error.JwtInvalidError('token is missing iat claim')
    if raw_jwt.issued_at() > now + validator.clock_skew():
      raise _jwt_error.JwtInvalidError(
          'token has a invalid iat claim in the future: %s' %
          raw_jwt.issued_at())
  if validator.has_expected_type_header():
    if not raw_jwt.has_type_header():
      raise _jwt_error.JwtInvalidError(
          'invalid JWT; missing expected type header %s.' %
          validator.expected_type_header())
    if validator.expected_type_header() != raw_jwt.type_header():
      raise _jwt_error.JwtInvalidError(
          'invalid JWT; expected type header %s, but got %s' %
          (validator.expected_type_header(), raw_jwt.type_header()))
  else:
    if raw_jwt.has_type_header() and not validator.ignore_type_header():
      raise _jwt_error.JwtInvalidError(
          'invalid JWT; token has type_header set, but validator not.')
  if validator.has_expected_issuer():
    if not raw_jwt.has_issuer():
      raise _jwt_error.JwtInvalidError(
          'invalid JWT; missing expected issuer %s.' %
          validator.expected_issuer())
    if validator.expected_issuer() != raw_jwt.issuer():
      raise _jwt_error.JwtInvalidError(
          'invalid JWT; expected issuer %s, but got %s' %
          (validator.expected_issuer(), raw_jwt.issuer()))
  else:
    if raw_jwt.has_issuer() and not validator.ignore_issuer():
      raise _jwt_error.JwtInvalidError(
          'invalid JWT; token has issuer set, but validator not.')
  if validator.has_expected_audience():
    if (not raw_jwt.has_audiences() or
        validator.expected_audience() not in raw_jwt.audiences()):
      raise _jwt_error.JwtInvalidError(
          'invalid JWT; missing expected audience %s.' %
          validator.expected_audience())
  else:
    if raw_jwt.has_audiences() and not validator.ignore_audiences():
      raise _jwt_error.JwtInvalidError(
          'invalid JWT; token has audience set, but validator not.')
