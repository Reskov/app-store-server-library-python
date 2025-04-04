# Copyright (c) 2023 Apple Inc. Licensed under MIT License.

import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

from appstoreserverlibrary.signed_data_verifier import _ChainVerifier, VerificationException, VerificationStatus
from base64 import b64decode, b64encode

ROOT_CA_BASE64_ENCODED = "MIIBgjCCASmgAwIBAgIJALUc5ALiH5pbMAoGCCqGSM49BAMDMDYxCzAJBgNVBAYTAlVTMRMwEQYDVQQIDApDYWxpZm9ybmlhMRIwEAYDVQQHDAlDdXBlcnRpbm8wHhcNMjMwMTA1MjEzMDIyWhcNMzMwMTAyMjEzMDIyWjA2MQswCQYDVQQGEwJVUzETMBEGA1UECAwKQ2FsaWZvcm5pYTESMBAGA1UEBwwJQ3VwZXJ0aW5vMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEc+/Bl+gospo6tf9Z7io5tdKdrlN1YdVnqEhEDXDShzdAJPQijamXIMHf8xWWTa1zgoYTxOKpbuJtDplz1XriTaMgMB4wDAYDVR0TBAUwAwEB/zAOBgNVHQ8BAf8EBAMCAQYwCgYIKoZIzj0EAwMDRwAwRAIgemWQXnMAdTad2JDJWng9U4uBBL5mA7WI05H7oH7c6iQCIHiRqMjNfzUAyiu9h6rOU/K+iTR0I/3Y/NSWsXHX+acc"
INTERMEDIATE_CA_BASE64_ENCODED = "MIIBnzCCAUWgAwIBAgIBCzAKBggqhkjOPQQDAzA2MQswCQYDVQQGEwJVUzETMBEGA1UECAwKQ2FsaWZvcm5pYTESMBAGA1UEBwwJQ3VwZXJ0aW5vMB4XDTIzMDEwNTIxMzEwNVoXDTMzMDEwMTIxMzEwNVowRTELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMRIwEAYDVQQHDAlDdXBlcnRpbm8xFTATBgNVBAoMDEludGVybWVkaWF0ZTBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABBUN5V9rKjfRiMAIojEA0Av5Mp0oF+O0cL4gzrTF178inUHugj7Et46NrkQ7hKgMVnjogq45Q1rMs+cMHVNILWqjNTAzMA8GA1UdEwQIMAYBAf8CAQAwDgYDVR0PAQH/BAQDAgEGMBAGCiqGSIb3Y2QGAgEEAgUAMAoGCCqGSM49BAMDA0gAMEUCIQCmsIKYs41ullssHX4rVveUT0Z7Is5/hLK1lFPTtun3hAIgc2+2RG5+gNcFVcs+XJeEl4GZ+ojl3ROOmll+ye7dynQ="
LEAF_CERT_BASE64_ENCODED = "MIIBoDCCAUagAwIBAgIBDDAKBggqhkjOPQQDAzBFMQswCQYDVQQGEwJVUzELMAkGA1UECAwCQ0ExEjAQBgNVBAcMCUN1cGVydGlubzEVMBMGA1UECgwMSW50ZXJtZWRpYXRlMB4XDTIzMDEwNTIxMzEzNFoXDTMzMDEwMTIxMzEzNFowPTELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMRIwEAYDVQQHDAlDdXBlcnRpbm8xDTALBgNVBAoMBExlYWYwWTATBgcqhkjOPQIBBggqhkjOPQMBBwNCAATitYHEaYVuc8g9AjTOwErMvGyPykPa+puvTI8hJTHZZDLGas2qX1+ErxgQTJgVXv76nmLhhRJH+j25AiAI8iGsoy8wLTAJBgNVHRMEAjAAMA4GA1UdDwEB/wQEAwIHgDAQBgoqhkiG92NkBgsBBAIFADAKBggqhkjOPQQDAwNIADBFAiBX4c+T0Fp5nJ5QRClRfu5PSByRvNPtuaTsk0vPB3WAIAIhANgaauAj/YP9s0AkEhyJhxQO/6Q2zouZ+H1CIOehnMzQ"

INTERMEDIATE_CA_INVALID_OID_BASE64_ENCODED = "MIIBnjCCAUWgAwIBAgIBDTAKBggqhkjOPQQDAzA2MQswCQYDVQQGEwJVUzETMBEGA1UECAwKQ2FsaWZvcm5pYTESMBAGA1UEBwwJQ3VwZXJ0aW5vMB4XDTIzMDEwNTIxMzYxNFoXDTMzMDEwMTIxMzYxNFowRTELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMRIwEAYDVQQHDAlDdXBlcnRpbm8xFTATBgNVBAoMDEludGVybWVkaWF0ZTBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABBUN5V9rKjfRiMAIojEA0Av5Mp0oF+O0cL4gzrTF178inUHugj7Et46NrkQ7hKgMVnjogq45Q1rMs+cMHVNILWqjNTAzMA8GA1UdEwQIMAYBAf8CAQAwDgYDVR0PAQH/BAQDAgEGMBAGCiqGSIb3Y2QGAgIEAgUAMAoGCCqGSM49BAMDA0cAMEQCIFROtTE+RQpKxNXETFsf7Mc0h+5IAsxxo/X6oCC/c33qAiAmC5rn5yCOOEjTY4R1H1QcQVh+eUwCl13NbQxWCuwxxA=="
LEAF_CERT_FOR_INTERMEDIATE_CA_INVALID_OID_BASE64_ENCODED = "MIIBnzCCAUagAwIBAgIBDjAKBggqhkjOPQQDAzBFMQswCQYDVQQGEwJVUzELMAkGA1UECAwCQ0ExEjAQBgNVBAcMCUN1cGVydGlubzEVMBMGA1UECgwMSW50ZXJtZWRpYXRlMB4XDTIzMDEwNTIxMzY1OFoXDTMzMDEwMTIxMzY1OFowPTELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMRIwEAYDVQQHDAlDdXBlcnRpbm8xDTALBgNVBAoMBExlYWYwWTATBgcqhkjOPQIBBggqhkjOPQMBBwNCAATitYHEaYVuc8g9AjTOwErMvGyPykPa+puvTI8hJTHZZDLGas2qX1+ErxgQTJgVXv76nmLhhRJH+j25AiAI8iGsoy8wLTAJBgNVHRMEAjAAMA4GA1UdDwEB/wQEAwIHgDAQBgoqhkiG92NkBgsBBAIFADAKBggqhkjOPQQDAwNHADBEAiAUAs+gzYOsEXDwQquvHYbcVymyNqDtGw9BnUFp2YLuuAIgXxQ3Ie9YU0cMqkeaFd+lyo0asv9eyzk6stwjeIeOtTU="
LEAF_CERT_INVALID_OID_BASE64_ENCODED = "MIIBoDCCAUagAwIBAgIBDzAKBggqhkjOPQQDAzBFMQswCQYDVQQGEwJVUzELMAkGA1UECAwCQ0ExEjAQBgNVBAcMCUN1cGVydGlubzEVMBMGA1UECgwMSW50ZXJtZWRpYXRlMB4XDTIzMDEwNTIxMzczMVoXDTMzMDEwMTIxMzczMVowPTELMAkGA1UEBhMCVVMxCzAJBgNVBAgMAkNBMRIwEAYDVQQHDAlDdXBlcnRpbm8xDTALBgNVBAoMBExlYWYwWTATBgcqhkjOPQIBBggqhkjOPQMBBwNCAATitYHEaYVuc8g9AjTOwErMvGyPykPa+puvTI8hJTHZZDLGas2qX1+ErxgQTJgVXv76nmLhhRJH+j25AiAI8iGsoy8wLTAJBgNVHRMEAjAAMA4GA1UdDwEB/wQEAwIHgDAQBgoqhkiG92NkBgsCBAIFADAKBggqhkjOPQQDAwNIADBFAiAb+7S3i//bSGy7skJY9+D4VgcQLKFeYfIMSrUCmdrFqwIhAIMVwzD1RrxPRtJyiOCXLyibIvwcY+VS73HYfk0O9lgz"

LEAF_CERT_PUBLIC_KEY = "-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE4rWBxGmFbnPIPQI0zsBKzLxsj8pD\n2vqbr0yPISUx2WQyxmrNql9fhK8YEEyYFV7++p5i4YUSR/o9uQIgCPIhrA==\n-----END PUBLIC KEY-----\n"

REAL_APPLE_ROOT_BASE64_ENCODED = "MIICQzCCAcmgAwIBAgIILcX8iNLFS5UwCgYIKoZIzj0EAwMwZzEbMBkGA1UEAwwSQXBwbGUgUm9vdCBDQSAtIEczMSYwJAYDVQQLDB1BcHBsZSBDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eTETMBEGA1UECgwKQXBwbGUgSW5jLjELMAkGA1UEBhMCVVMwHhcNMTQwNDMwMTgxOTA2WhcNMzkwNDMwMTgxOTA2WjBnMRswGQYDVQQDDBJBcHBsZSBSb290IENBIC0gRzMxJjAkBgNVBAsMHUFwcGxlIENlcnRpZmljYXRpb24gQXV0aG9yaXR5MRMwEQYDVQQKDApBcHBsZSBJbmMuMQswCQYDVQQGEwJVUzB2MBAGByqGSM49AgEGBSuBBAAiA2IABJjpLz1AcqTtkyJygRMc3RCV8cWjTnHcFBbZDuWmBSp3ZHtfTjjTuxxEtX/1H7YyYl3J6YRbTzBPEVoA/VhYDKX1DyxNB0cTddqXl5dvMVztK517IDvYuVTZXpmkOlEKMaNCMEAwHQYDVR0OBBYEFLuw3qFYM4iapIqZ3r6966/ayySrMA8GA1UdEwEB/wQFMAMBAf8wDgYDVR0PAQH/BAQDAgEGMAoGCCqGSM49BAMDA2gAMGUCMQCD6cHEFl4aXTQY2e3v9GwOAEZLuN+yRhHFD/3meoyhpmvOwgPUnPWTxnS4at+qIxUCMG1mihDK1A3UT82NQz60imOlM27jbdoXt2QfyFMm+YhidDkLF1vLUagM6BgD56KyKA=="
REAL_APPLE_INTERMEDIATE_BASE64_ENCODED = "MIIDFjCCApygAwIBAgIUIsGhRwp0c2nvU4YSycafPTjzbNcwCgYIKoZIzj0EAwMwZzEbMBkGA1UEAwwSQXBwbGUgUm9vdCBDQSAtIEczMSYwJAYDVQQLDB1BcHBsZSBDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eTETMBEGA1UECgwKQXBwbGUgSW5jLjELMAkGA1UEBhMCVVMwHhcNMjEwMzE3MjAzNzEwWhcNMzYwMzE5MDAwMDAwWjB1MUQwQgYDVQQDDDtBcHBsZSBXb3JsZHdpZGUgRGV2ZWxvcGVyIFJlbGF0aW9ucyBDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eTELMAkGA1UECwwCRzYxEzARBgNVBAoMCkFwcGxlIEluYy4xCzAJBgNVBAYTAlVTMHYwEAYHKoZIzj0CAQYFK4EEACIDYgAEbsQKC94PrlWmZXnXgtxzdVJL8T0SGYngDRGpngn3N6PT8JMEb7FDi4bBmPhCnZ3/sq6PF/cGcKXWsL5vOteRhyJ45x3ASP7cOB+aao90fcpxSv/EZFbniAbNgZGhIhpIo4H6MIH3MBIGA1UdEwEB/wQIMAYBAf8CAQAwHwYDVR0jBBgwFoAUu7DeoVgziJqkipnevr3rr9rLJKswRgYIKwYBBQUHAQEEOjA4MDYGCCsGAQUFBzABhipodHRwOi8vb2NzcC5hcHBsZS5jb20vb2NzcDAzLWFwcGxlcm9vdGNhZzMwNwYDVR0fBDAwLjAsoCqgKIYmaHR0cDovL2NybC5hcHBsZS5jb20vYXBwbGVyb290Y2FnMy5jcmwwHQYDVR0OBBYEFD8vlCNR01DJmig97bB85c+lkGKZMA4GA1UdDwEB/wQEAwIBBjAQBgoqhkiG92NkBgIBBAIFADAKBggqhkjOPQQDAwNoADBlAjBAXhSq5IyKogMCPtw490BaB677CaEGJXufQB/EqZGd6CSjiCtOnuMTbXVXmxxcxfkCMQDTSPxarZXvNrkxU3TkUMI33yzvFVVRT4wxWJC994OsdcZ4+RGNsYDyR5gmdr0nDGg="
REAL_APPLE_SIGNING_CERTIFICATE_BASE64_ENCODED = "MIIEMDCCA7agAwIBAgIQaPoPldvpSoEH0lBrjDPv9jAKBggqhkjOPQQDAzB1MUQwQgYDVQQDDDtBcHBsZSBXb3JsZHdpZGUgRGV2ZWxvcGVyIFJlbGF0aW9ucyBDZXJ0aWZpY2F0aW9uIEF1dGhvcml0eTELMAkGA1UECwwCRzYxEzARBgNVBAoMCkFwcGxlIEluYy4xCzAJBgNVBAYTAlVTMB4XDTIxMDgyNTAyNTAzNFoXDTIzMDkyNDAyNTAzM1owgZIxQDA+BgNVBAMMN1Byb2QgRUNDIE1hYyBBcHAgU3RvcmUgYW5kIGlUdW5lcyBTdG9yZSBSZWNlaXB0IFNpZ25pbmcxLDAqBgNVBAsMI0FwcGxlIFdvcmxkd2lkZSBEZXZlbG9wZXIgUmVsYXRpb25zMRMwEQYDVQQKDApBcHBsZSBJbmMuMQswCQYDVQQGEwJVUzBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABOoTcaPcpeipNL9eQ06tCu7pUcwdCXdN8vGqaUjd58Z8tLxiUC0dBeA+euMYggh1/5iAk+FMxUFmA2a1r4aCZ8SjggIIMIICBDAMBgNVHRMBAf8EAjAAMB8GA1UdIwQYMBaAFD8vlCNR01DJmig97bB85c+lkGKZMHAGCCsGAQUFBwEBBGQwYjAtBggrBgEFBQcwAoYhaHR0cDovL2NlcnRzLmFwcGxlLmNvbS93d2RyZzYuZGVyMDEGCCsGAQUFBzABhiVodHRwOi8vb2NzcC5hcHBsZS5jb20vb2NzcDAzLXd3ZHJnNjAyMIIBHgYDVR0gBIIBFTCCAREwggENBgoqhkiG92NkBQYBMIH+MIHDBggrBgEFBQcCAjCBtgyBs1JlbGlhbmNlIG9uIHRoaXMgY2VydGlmaWNhdGUgYnkgYW55IHBhcnR5IGFzc3VtZXMgYWNjZXB0YW5jZSBvZiB0aGUgdGhlbiBhcHBsaWNhYmxlIHN0YW5kYXJkIHRlcm1zIGFuZCBjb25kaXRpb25zIG9mIHVzZSwgY2VydGlmaWNhdGUgcG9saWN5IGFuZCBjZXJ0aWZpY2F0aW9uIHByYWN0aWNlIHN0YXRlbWVudHMuMDYGCCsGAQUFBwIBFipodHRwOi8vd3d3LmFwcGxlLmNvbS9jZXJ0aWZpY2F0ZWF1dGhvcml0eS8wHQYDVR0OBBYEFCOCmMBq//1L5imvVmqX1oCYeqrMMA4GA1UdDwEB/wQEAwIHgDAQBgoqhkiG92NkBgsBBAIFADAKBggqhkjOPQQDAwNoADBlAjEAl4JB9GJHixP2nuibyU1k3wri5psGIxPME05sFKq7hQuzvbeyBu82FozzxmbzpogoAjBLSFl0dZWIYl2ejPV+Di5fBnKPu8mymBQtoE/H2bES0qAs8bNueU3CBjjh1lwnDsI="

EFFECTIVE_DATE = 1681312846
CLOCK_DATE = 41231

class X509Verification(unittest.TestCase):
    def test_valid_chain_without_ocsp(self):
        verifier = _ChainVerifier([b64decode(ROOT_CA_BASE64_ENCODED)], False)
        public_key = verifier.verify_chain([
            LEAF_CERT_BASE64_ENCODED,
            INTERMEDIATE_CA_BASE64_ENCODED,
            ROOT_CA_BASE64_ENCODED
        ], False, EFFECTIVE_DATE)
        self.assertEqual(LEAF_CERT_PUBLIC_KEY, public_key)

    def test_valid_chain_invalid_intermediate_OID_without_OCSP(self):
        verifier = _ChainVerifier([b64decode(ROOT_CA_BASE64_ENCODED)], False)
        with self.assertRaises(VerificationException) as context:
            verifier.verify_chain([
                LEAF_CERT_FOR_INTERMEDIATE_CA_INVALID_OID_BASE64_ENCODED,
                INTERMEDIATE_CA_INVALID_OID_BASE64_ENCODED,
                ROOT_CA_BASE64_ENCODED
            ], False, EFFECTIVE_DATE)
        self.assertEqual(VerificationStatus.VERIFICATION_FAILURE, context.exception.status)

    def test_valid_chain_invalid_leaf_OID_without_OCSP(self):
        verifier = _ChainVerifier([b64decode(ROOT_CA_BASE64_ENCODED)], False)
        with self.assertRaises(VerificationException) as context:
            verifier.verify_chain([
                LEAF_CERT_INVALID_OID_BASE64_ENCODED,
                INTERMEDIATE_CA_BASE64_ENCODED,
                ROOT_CA_BASE64_ENCODED
            ], False, EFFECTIVE_DATE)
        self.assertEqual(VerificationStatus.VERIFICATION_FAILURE, context.exception.status)

    def test_invalid_chain_length(self):
        verifier = _ChainVerifier([b64decode(ROOT_CA_BASE64_ENCODED)], False)
        with self.assertRaises(VerificationException) as context:
            verifier.verify_chain([INTERMEDIATE_CA_BASE64_ENCODED, ROOT_CA_BASE64_ENCODED], False, EFFECTIVE_DATE)
        self.assertIn('Verification failed with status INVALID_CHAIN_LENGTH', str(context.exception))

    def test_invalid_base64_in_certificate_list(self):
        verifier = _ChainVerifier([b64decode(ROOT_CA_BASE64_ENCODED)])
        with self.assertRaises(VerificationException) as context:
            verifier.verify_chain([
                "abc",
                INTERMEDIATE_CA_BASE64_ENCODED,
                ROOT_CA_BASE64_ENCODED
            ], False, EFFECTIVE_DATE)
        self.assertEqual(VerificationStatus.INVALID_CERTIFICATE, context.exception.status)

    def test_invalid_data_in_certificate_list(self):
        verifier = _ChainVerifier([b64decode(ROOT_CA_BASE64_ENCODED)], False)
        with self.assertRaises(VerificationException) as context:
            verifier.verify_chain([
                str(b64encode(b"abc")),
                INTERMEDIATE_CA_BASE64_ENCODED,
                ROOT_CA_BASE64_ENCODED
            ], False, EFFECTIVE_DATE)
        self.assertEqual(VerificationStatus.INVALID_CERTIFICATE, context.exception.status)
    def test_malformed_root_cert(self):
        verifier = _ChainVerifier([b64decode(b64encode(b"abc"))])
        with self.assertRaises(Exception) as context:
            verifier.verify_chain([
                LEAF_CERT_BASE64_ENCODED,
                INTERMEDIATE_CA_BASE64_ENCODED,
                ROOT_CA_BASE64_ENCODED
            ], False, EFFECTIVE_DATE)
        self.assertEqual(VerificationStatus.INVALID_CERTIFICATE, context.exception.status)

    def test_chain_different_than_root_certificate(self):
        verifier = _ChainVerifier([b64decode(REAL_APPLE_ROOT_BASE64_ENCODED)], False)

        with self.assertRaises(Exception) as context:
            verifier.verify_chain([
                LEAF_CERT_BASE64_ENCODED,
                INTERMEDIATE_CA_BASE64_ENCODED,
                ROOT_CA_BASE64_ENCODED
            ], False, EFFECTIVE_DATE)
        self.assertEqual(VerificationStatus.VERIFICATION_FAILURE, context.exception.status)

    def test_valid_expired_chain(self):
        verifier = _ChainVerifier([b64decode(ROOT_CA_BASE64_ENCODED)], False)
        with self.assertRaises(VerificationException) as context:
            verifier.verify_chain([
                LEAF_CERT_BASE64_ENCODED,
                INTERMEDIATE_CA_BASE64_ENCODED,
                ROOT_CA_BASE64_ENCODED
            ], False, 2280946846)
        self.assertEqual(VerificationStatus.VERIFICATION_FAILURE, context.exception.status)

    def test_apple_chain_is_valid_with_ocsp_and_strict(self):
        verifier = _ChainVerifier([b64decode(REAL_APPLE_ROOT_BASE64_ENCODED)])
        verifier.verify_chain([
            REAL_APPLE_SIGNING_CERTIFICATE_BASE64_ENCODED,
            REAL_APPLE_INTERMEDIATE_BASE64_ENCODED,
            REAL_APPLE_ROOT_BASE64_ENCODED
        ], True, EFFECTIVE_DATE)

    def test_ocsp_response_caching(self):
        verifier = _ChainVerifier([b64decode(REAL_APPLE_ROOT_BASE64_ENCODED)])
        magic_mock = MagicMock(return_value=LEAF_CERT_BASE64_ENCODED)
        verifier._verify_chain_without_caching = magic_mock
        with patch('time.time', mock.MagicMock(return_value=CLOCK_DATE)):
            verifier.verify_chain([
                REAL_APPLE_SIGNING_CERTIFICATE_BASE64_ENCODED,
                REAL_APPLE_INTERMEDIATE_BASE64_ENCODED,
                REAL_APPLE_ROOT_BASE64_ENCODED
            ], True, EFFECTIVE_DATE)
        self.assertEqual(1, magic_mock.call_count)
        with patch('time.time', mock.MagicMock(return_value=CLOCK_DATE + 1)): # 1 second
            verifier.verify_chain([
                REAL_APPLE_SIGNING_CERTIFICATE_BASE64_ENCODED,
                REAL_APPLE_INTERMEDIATE_BASE64_ENCODED,
                REAL_APPLE_ROOT_BASE64_ENCODED
            ], True, EFFECTIVE_DATE)
        self.assertEqual(1, magic_mock.call_count)

    def test_ocsp_response_caching_has_expiration(self):
        verifier = _ChainVerifier([b64decode(REAL_APPLE_ROOT_BASE64_ENCODED)])
        magic_mock = MagicMock(return_value=LEAF_CERT_BASE64_ENCODED)
        verifier._verify_chain_without_caching = magic_mock
        with patch('time.time', mock.MagicMock(return_value=CLOCK_DATE)):
            verifier.verify_chain([
                REAL_APPLE_SIGNING_CERTIFICATE_BASE64_ENCODED,
                REAL_APPLE_INTERMEDIATE_BASE64_ENCODED,
                REAL_APPLE_ROOT_BASE64_ENCODED
            ], True, EFFECTIVE_DATE)
        self.assertEqual(1, magic_mock.call_count)
        with patch('time.time', mock.MagicMock(return_value=CLOCK_DATE + 900)): # 15 minutes
            verifier.verify_chain([
                REAL_APPLE_SIGNING_CERTIFICATE_BASE64_ENCODED,
                REAL_APPLE_INTERMEDIATE_BASE64_ENCODED,
                REAL_APPLE_ROOT_BASE64_ENCODED
            ], True, EFFECTIVE_DATE)
        self.assertEqual(2, magic_mock.call_count)

    def test_ocsp_response_caching_with_different_chain(self):
        verifier = _ChainVerifier([b64decode(REAL_APPLE_ROOT_BASE64_ENCODED)])
        magic_mock = MagicMock(return_value=LEAF_CERT_BASE64_ENCODED)
        verifier._verify_chain_without_caching = magic_mock
        with patch('time.time', mock.MagicMock(return_value=CLOCK_DATE)):
            verifier.verify_chain([
                LEAF_CERT_BASE64_ENCODED,
                INTERMEDIATE_CA_BASE64_ENCODED,
                ROOT_CA_BASE64_ENCODED
            ], True, EFFECTIVE_DATE)
        self.assertEqual(1, magic_mock.call_count)
        with patch('time.time', mock.MagicMock(return_value=CLOCK_DATE)): # Same
            verifier.verify_chain([
                REAL_APPLE_SIGNING_CERTIFICATE_BASE64_ENCODED,
                REAL_APPLE_INTERMEDIATE_BASE64_ENCODED,
                REAL_APPLE_ROOT_BASE64_ENCODED
            ], True, EFFECTIVE_DATE)
        self.assertEqual(2, magic_mock.call_count)

    def test_ocsp_response_caching_with_slightly_different_chain(self):
        verifier = _ChainVerifier([b64decode(REAL_APPLE_ROOT_BASE64_ENCODED)])
        magic_mock = MagicMock(return_value=LEAF_CERT_BASE64_ENCODED)
        verifier._verify_chain_without_caching = magic_mock
        with patch('time.time', mock.MagicMock(return_value=CLOCK_DATE)):
            verifier.verify_chain([
                LEAF_CERT_BASE64_ENCODED,
                INTERMEDIATE_CA_BASE64_ENCODED,
                ROOT_CA_BASE64_ENCODED
            ], True, EFFECTIVE_DATE)
        self.assertEqual(1, magic_mock.call_count)
        with patch('time.time', mock.MagicMock(return_value=CLOCK_DATE)): # Same
            verifier.verify_chain([
                LEAF_CERT_BASE64_ENCODED,
                INTERMEDIATE_CA_BASE64_ENCODED,
                REAL_APPLE_ROOT_BASE64_ENCODED
            ], True, EFFECTIVE_DATE)
        self.assertEqual(2, magic_mock.call_count)


if __name__ == '__main__':
    unittest.main()
