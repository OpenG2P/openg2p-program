# Map Form To Program

## Introduction

In this repo you can map form to the program. So, that someone applying into your program can fill you form
that you have mapped with program. This form is the website page where you can crete a form using the website
module functionality.

## Steps

### Modification in the model

- A new field will be added in `g2p.program` model where you can store the view id of the website page.
- The new field will be of "Many2One" type and has co-model which is `website.page` model.
- So, in this field we need to remove '/contact-us', '/home', '/contactus-thank-you' basically all the page
  only the application page will be their. And this can be achieved by domain attribute:

      domain=[('id', 'not in', [value1, value2, ....])]

- When the form_id will be saved in `g2p.program` model at that the base template should also be changed to
  the custom form template that you can define.

      @api.constrains('<new_field_name>')
      def update_form_template(self):
        # custom logic

- In the custom logic you can update the **t-call** parameter value and can insert the **csrf_token()** div
  element in the form template.

### Modification in view

This new field can be added to the view by inheriting the parent view and using 'xpath' experssion and giving
a position where to inherit this field.

**Note**: If someone has applied to program and then you don't want change the form mapping, you can set field
as readonly by `attrs` attribute in the field.

You can also add this field in the create form wizard. So, that while creating the program only we can map a
form to that program.
