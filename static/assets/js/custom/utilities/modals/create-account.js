// Define a function to create a form validation instance
function createFormValidation(form, fields) {
    return FormValidation.formValidation(form, {
        fields: fields,
        plugins: {
            trigger: new FormValidation.plugins.Trigger,
            bootstrap: new FormValidation.plugins.Bootstrap5({
                rowSelector: ".fv-row",
                eleInvalidClass: "",
                eleValidClass: ""
            })
        }
    });
}

// Define a function to handle the stepper's next event
function handleStepperNext(stepper, currentStepIndex, validations) {
    const validation = validations[currentStepIndex - 1];
    if (validation) {
        validation.validate().then((result) => {
            if (result === "Valid") {
                stepper.goNext();
                KTUtil.scrollTop();
            } else {
                Swal.fire({
                    text: "Sorry, looks like there are some errors detected, please try again.",
                    icon: "error",
                    buttonsStyling: false,
                    confirmButtonText: "Ok, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                }).then(() => {
                    KTUtil.scrollTop();
                });
            }
        });
    } else {
        stepper.goNext();
        KTUtil.scrollTop();
    }
}

// Define the KTCreateAccount function
var KTCreateAccount = function() {
    var stepperElement = document.querySelector("#kt_create_account_stepper");
    var formElement = stepperElement.querySelector("#kt_create_account_form");
    var submitButton = stepperElement.querySelector('[data-kt-stepper-action="submit"]');
    var nextButton = stepperElement.querySelector('[data-kt-stepper-action="next"]');
    var stepper = new KTStepper(stepperElement);
    var validations = [];

    // Create form validation instances
    if (formElement.querySelector('[name="csv_file_url"]')) {
        validations.push(createFormValidation(formElement, {
            csv_file_url: {
                validators: {
                    notEmpty: {
                        message: "CSV file URL is required"
                    }
                }
            }
        }));
    } else if (formElement.querySelector('[name="sales_url"]')) {
        validations.push(createFormValidation(formElement, {
            sales_url: {
                validators: {
                    notEmpty: {
                        message: "Sales Navigator search URL is required"
                    }
                }
            }
        }));
    }
    validations.push(createFormValidation(formElement, {
        session_cookie: {
            validators: {
                notEmpty: {
                    message: "Session cookie is required"
                }
            }
        }
    }));
    // Assuming you might want another validation for the final step
    validations.push(createFormValidation(formElement, {
        final_step_field: {
            validators: {
                notEmpty: {
                    message: "Final step field is required"
                }
            }
        }
    }));

    // Handle stepper events
    stepper.on("kt.stepper.changed", (event) => {
        const currentStepIndex = stepper.getCurrentStepIndex();
        if (currentStepIndex === 4) {
            submitButton.classList.remove("d-none");
            submitButton.classList.add("d-inline-block");
            nextButton.classList.add("d-none");
        } else if (currentStepIndex === 5) {
            submitButton.classList.add("d-none");
            nextButton.classList.add("d-none");
        } else {
            submitButton.classList.remove("d-inline-block");
            submitButton.classList.remove("d-none");
            nextButton.classList.remove("d-none");
        }
    });

    stepper.on("kt.stepper.next", (event) => {
        handleStepperNext(stepper, stepper.getCurrentStepIndex(), validations);
    });

    stepper.on("kt.stepper.previous", (event) => {
        stepper.goPrevious();
        KTUtil.scrollTop();
    });

    // Handle submit button click
    // Handle submit button click
submitButton.addEventListener("click", (event) => {
    event.preventDefault(); // Prevent default form submission

    // Ensure the validation instance index is correct
    const validation = validations[2]; // Assuming the final validation is at index 2

    validation.validate().then((result) => {
        if (result === "Valid") {
            // Show the loading indicator on the submit button
            submitButton.disabled = true;
            submitButton.setAttribute("data-kt-indicator", "on");

            // Create a new FormData object from the form
            const formData = new FormData(formElement);

            // Create an XMLHttpRequest to send the form data
            const xhr = new XMLHttpRequest();
            xhr.open("POST", formElement.action, true);

            // Add CSRF token if needed
            xhr.setRequestHeader("X-CSRFToken", document.querySelector('input[name="csrfmiddlewaretoken"]').value);

            xhr.onload = () => {
                // Remove the loading indicator
                submitButton.removeAttribute("data-kt-indicator");
                submitButton.disabled = false;

                if (xhr.status >= 200 && xhr.status < 300) {
                    // Handle successful response (redirect or update UI as needed)
                    // Example: Redirect to a new URL
                    window.location.href = xhr.responseURL; // Adjust based on your requirements
                } else {
                    // Handle errors
                    Swal.fire({
                        text: "Sorry, something went wrong. Please try again.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn btn-primary"
                        }
                    }).then(() => {
                        KTUtil.scrollTop();
                    });
                }
            };

            xhr.onerror = () => {
                // Handle network errors
                Swal.fire({
                    text: "Sorry, there was a network error. Please try again.",
                    icon: "error",
                    buttonsStyling: false,
                    confirmButtonText: "Ok, got it!",
                    customClass: {
                        confirmButton: "btn btn-primary"
                    }
                }).then(() => {
                    KTUtil.scrollTop();
                });
            };

            // Send the form data
            xhr.send(formData);

        } else {
            // Show error message if validation fails
            Swal.fire({
                text: "Sorry, looks like there are some errors detected, please try again.",
                icon: "error",
                buttonsStyling: false,
                confirmButtonText: "Ok, got it!",
                customClass: {
                    confirmButton: "btn btn-primary"
                }
            }).then(() => {
                KTUtil.scrollTop();
            });
        }
    });
});
}();