{
  "name": .name,
  "is_group": .isGroup,
  "address": .address,
  "registration_date": .registrationDate,
  "group_membership_ids": (
    if .groupMembershipIds? then
      [
        .groupMembershipIds[] | {
          "individual": {
            "name": .individual.name,
            "given_name": .individual.givenName,
            "family_name": .individual.familyName,
            "addl_name": .individual.addlName,
            "email": .individual.email,
            "address": .individual.address,
            "registration_date": .individual.registrationDate,
            "birth_place": .individual.birthPlace,
            "birthdate": .individual.birthdate,
            "create_date": .individual.createDate,
            "write_date": .individual.writeDate,
            "reg_ids": (
              if .individual.regIds? then
                [.individual.regIds[] | {id_type: {name:.idTypeAsStr}, value: .value}]
              else
                []
              end
            ),
            "phone_number_ids": (
              if .individual.phoneNumberIds? then
                [.individual.phoneNumberIds[] | {
                  phone_no: .phoneNo,
                  phone_sanitized: .phoneSanitized,
                  date_collected: .dateCollected,
                  disabled: .disabled
                }]
              else
                []
              end
            )
          },
          "kind": {name:.kind.name}
        }
      ]
    else
      []
    end
  ),
  "reg_ids": (
    if .regIds? then
      [.regIds[] | {id_type: {name:.idTypeAsStr}, value: .value}]
    else
      []
    end
  ),
  "phone_number_ids": (
    if .phoneNumberIds? then
      [.phoneNumberIds[] | {
        phone_no: .phoneNo,
        phone_sanitized: .phoneSanitized,
        date_collected: .dateCollected,
        disabled: .disabled
      }]
    else
      []
    end
  )
}
