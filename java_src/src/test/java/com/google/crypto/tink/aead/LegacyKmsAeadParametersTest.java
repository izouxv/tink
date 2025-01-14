// Copyright 2023 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
////////////////////////////////////////////////////////////////////////////////

package com.google.crypto.tink.aead;

import static com.google.common.truth.Truth.assertThat;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

@RunWith(JUnit4.class)
public final class LegacyKmsAeadParametersTest {
  @Test
  public void testCreateValue() throws Exception {
    LegacyKmsAeadParameters parameters = LegacyKmsAeadParameters.create("someArbitrarykeyUri223");
    assertThat(parameters.keyUri()).isEqualTo("someArbitrarykeyUri223");
    assertThat(parameters.hasIdRequirement()).isFalse();
  }

  @Test
  public void testEqualsAndHashCode() throws Exception {
    LegacyKmsAeadParameters parameters1 = LegacyKmsAeadParameters.create("someArbitrarykeyUri223");
    LegacyKmsAeadParameters parameters1Copy =
        LegacyKmsAeadParameters.create("someArbitrarykeyUri223");
    LegacyKmsAeadParameters parameters2 = LegacyKmsAeadParameters.create("someArbitrarykeyUri112");

    assertThat(parameters1).isEqualTo(parameters1Copy);
    assertThat(parameters1).isNotEqualTo(parameters2);

    assertThat(parameters1.hashCode()).isEqualTo(parameters1Copy.hashCode());
    assertThat(parameters1.hashCode()).isNotEqualTo(parameters2.hashCode());
  }
}
