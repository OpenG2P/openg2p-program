[
    {
        "id": .credential_type,
        "format": .supported_format,
        "scope": .scope,
        "cryptographic_binding_methods_supported": [
            "did:jwk"
        ],
        "credential_signing_alg_values_supported": [
            "RS256"
        ],
        "proof_types_supported": [
            "jwt"
        ],
        "credential_definition": {
            "type": [
                "VerifiableCredential",
                .credential_type
            ],
            "credentialSubject": {
                "fullName": {
                    "display": [
                        {
                            "name": "Name",
                            "locale": "en"
                        }
                    ]
                },
                "gender": {
                    "display": [
                        {
                            "name": "Gender",
                            "locale": "en"
                        }
                    ]
                },
               "dateOfBirth": {
                    "display": [
                        {
                            "name": "Date of Birth",
                            "locale": "en"
                        }
                    ]
                },
                "address": {
                    "display": [
                        {
                            "name": "Address",
                            "locale": "en"
                        }
                    ]
                },
                "UIN": {
                    "display": [
                        {
                            "name": "Beneficiary ID",
                            "locale": "en"
                        }
                    ]
                },
                "nationalID": {
                    "display": [
                        {
                            "name": "National ID",
                            "locale": "en"
                        }
                    ]
                },
                "programName": {
                    "display": [
                        {
                            "name": "Program Name",
                            "locale": "en"
                        }
                    ]
                },
                "validUntil": {
                    "display": [
                        {
                            "name": "Valid until",
                            "locale": "en"
                        }
                    ]
                }
            }
        },
        "display": [
            {
                "name": "OpenG2P Program Beneficiary Credential",
                "locale": "en",
                "logo": {
                    "url": (.web_base_url + "/g2p_openid_vci_programs/static/description/icon.png"),
                    "alt_text": "a square logo of a OpenG2P"
                },
                "background_color": "#f5c538",
                "text_color": "#03096e"
            }
        ],
        "order": [
            "fullName",
            "programName",
            "gender",
            "dateOfBirth",
            "validUntil"
        ]
    }
]
