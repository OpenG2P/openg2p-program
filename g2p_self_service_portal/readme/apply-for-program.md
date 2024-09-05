# Self Service Portal-Apply for program

## Introduction

In this repo the logged in user can apply for the listed programs if they have not applied.

## Steps

When you go to list of all programs and apply for any of the program you will go to `/selfservice/apply`
controller along with the program_id as query parameter, where the following task will be performed:

- It will check for the form_id that is mapped with this program.
- If no form is mapped with the program, it will directly return a string "No form mapped with the program"
- Then we will update the url of the form page as `/selfservice/apply/form_id` and controller will return this
  url.
- At last we will pass the program_name and current_user_name as query parameter to the above url.

**\*\*Note\*\***: If form is not mapped with the program. Refer this repo [Form mapping with Program]() for
mapping form to program.

So, this controller will be redirected to the application form of the program and you can fill out the form
and can apply for the program or can cancel the application.

### When you `submit` the Applicaton

If you submit the application, onclick event listener of javacript will be triggerd and it will checking for
the required fields. If all required fields are not filled you will get a toast message in the top right side
with a error message to fill all the required fields. Along wih the toast message you will also get error
message beow the required field and there input box border color will also change.

    List of all the error messages:
       1. If type is checkbox and radio
           eror message: Please select <field_name>

           example: let say we have gender field and it is required but not filled then the error message will be- please select gender

       2. Remaining data type
           error message: Please enter <field_name>

Along with the required fields it will also check for the valid data type.

    List of all validation messages:
        1. data type is email
            validaton message: Please enter a valid email address

        2. data type is url
            validaton message: Please enter a valid url

        3. data type is tel
             validaton message: Please enter a valid telephone number

**\*\*Note\*\***: Both the error message and validation message will not be displayed simultaneously.

When all the required field and valid data type is entered the submit button will go to
`/selfservice/submitted` controller. In this controller following task will be executed:

- Form data will be saved in the json format in `additional_info` field which is present in `res.partner`
  model
- Now an application_id will be generated having submission date followed by 5 digit sequence number starting
  from 00001, e.g. 24012300001
- After generating application_id, you will check the current user partner_id and current program_id for which
  the user has applied and will the pass these 3 parameter (application_id, program_id and partner_id) to our
  `g2p.program.membership` model to create a new record.
- At last you will render `form submitted view` along with submission_date and application_id.

### When you `cancel` the Applicaton

If you cancel the application you will get a popup message with **discard** and **cancel** buttons. The cancel
button will cancel the popup and you can continue with the application form while clicking on the ‘discard’
button will redirect you to the all programs list and your filled data will not be saved.
