"use strict";

var KTUsersAddUser = function() {
    const modalElement = document.getElementById("kt_modal_add_user");
    const formElement = modalElement.querySelector("#kt_modal_add_user_form");
    const modal = new bootstrap.Modal(modalElement);

    return {
        init: function() {
            (function() {
                var formValidation = FormValidation.formValidation(formElement, {
                    fields: {
                        user_email: {
                            validators: {
                                notEmpty: {
                                    message: "Email address is required"
                                },
                                emailAddress: {
                                    message: "The input is not a valid email address"
                                }
                            }
                        },
                        password: {
                            validators: {
                                notEmpty: {
                                    message: "Password is required"
                                },
                                stringLength: {
                                    min: 8,
                                    message: "Password must be at least 8 characters long"
                                }
                            }
                        },
                        user_role: {
                            validators: {
                                notEmpty: {
                                    message: "User role is required"
                                }
                            }
                        }
                    },
                    plugins: {
                        trigger: new FormValidation.plugins.Trigger(),
                        bootstrap: new FormValidation.plugins.Bootstrap5({
                            rowSelector: ".fv-row",
                            eleInvalidClass: "",
                            eleValidClass: ""
                        })
                    }
                });

                const submitButton = modalElement.querySelector('[data-kt-users-modal-action="submit"]');
                submitButton.addEventListener("click", function(event) {
                    event.preventDefault();
                    formValidation.validate().then(function(status) {
                        if (status === "Valid") {
                            submitButton.setAttribute("data-kt-indicator", "on");
                            submitButton.disabled = true;

                            // AJAX submission
                            const formData = new FormData(formElement);
                            fetch(formElement.action, {
                                method: 'POST',
                                body: formData,
                                headers: {
                                    'X-CSRFToken': formElement.querySelector('[name=csrfmiddlewaretoken]').value // CSRF token
                                }
                            })
                            .then(response => response.json())
                            .then(data => {
                                submitButton.removeAttribute("data-kt-indicator");
                                submitButton.disabled = false;

                                if (data.error) {
                                    Swal.fire({
                                        text: data.error,
                                        icon: "error",
                                        buttonsStyling: false,
                                        confirmButtonText: "Ok, got it!",
                                        customClass: {
                                            confirmButton: "btn btn-primary"
                                        }
                                    });
                                } else {
                                    Swal.fire({
                                        text: data.message,
                                        icon: "success",
                                        buttonsStyling: false,
                                        confirmButtonText: "Ok, got it!",
                                        customClass: {
                                            confirmButton: "btn btn-primary"
                                        }
                                    }).then(function() {
                                        modal.hide();
                                        formElement.reset(); // Reset the form
                                        location.reload(); // Refresh the page
                                    });
                                }
                            })
                            .catch(error => {
                                submitButton.removeAttribute("data-kt-indicator");
                                submitButton.disabled = false;
                                Swal.fire({
                                    text: "An error occurred while submitting the form.",
                                    icon: "error",
                                    buttonsStyling: false,
                                    confirmButtonText: "Ok, got it!",
                                    customClass: {
                                        confirmButton: "btn btn-primary"
                                    }
                                });
                            });
                        } else {
                            Swal.fire({
                                text: "Sorry, looks like there are some errors detected, please try again.",
                                icon: "error",
                                buttonsStyling: false,
                                confirmButtonText: "Ok, got it!",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            });
                        }
                    });
                });

                modalElement.querySelector('[data-kt-users-modal-action="cancel"]').addEventListener("click", function(event) {
                    event.preventDefault();
                    Swal.fire({
                        text: "Are you sure you would like to cancel?",
                        icon: "warning",
                        showCancelButton: true,
                        buttonsStyling: false,
                        confirmButtonText: "Yes, cancel it!",
                        cancelButtonText: "No, return",
                        customClass: {
                            confirmButton: "btn btn-primary",
                            cancelButton: "btn btn-active-light"
                        }
                    }).then(function(result) {
                        if (result.value) {
                            formElement.reset();
                            modal.hide();
                        } else if (result.dismiss === Swal.DismissReason.cancel) {
                            Swal.fire({
                                text: "Your form has not been cancelled!",
                                icon: "error",
                                buttonsStyling: false,
                                confirmButtonText: "Ok, got it!",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            });
                        }
                    });
                });

                modalElement.querySelector('[data-kt-users-modal-action="close"]').addEventListener("click", function(event) {
                    event.preventDefault();
                    Swal.fire({
                        text: "Are you sure you would like to cancel?",
                        icon: "warning",
                        showCancelButton: true,
                        buttonsStyling: false,
                        confirmButtonText: "Yes, cancel it!",
                        cancelButtonText: "No, return",
                        customClass: {
                            confirmButton: "btn btn-primary",
                            cancelButton: "btn btn-active-light"
                        }
                    }).then(function(result) {
                        if (result.value) {
                            formElement.reset();
                            modal.hide();
                        } else if (result.dismiss === Swal.DismissReason.cancel) {
                            Swal.fire({
                                text: "Your form has not been cancelled!",
                                icon: "error",
                                buttonsStyling: false,
                                confirmButtonText: "Ok, got it!",
                                customClass: {
                                    confirmButton: "btn btn-primary"
                                }
                            });
                        }
                    });
                });
            })();
        }
    };
}();

KTUtil.onDOMContentLoaded(function() {
    KTUsersAddUser.init();
});
