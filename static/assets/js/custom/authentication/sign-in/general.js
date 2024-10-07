"use strict";
var KTSigninGeneral = function() {
    var form, submitButton, validator;
    return {
        init: function() {
            form = document.querySelector("#kt_sign_in_form");
            submitButton = document.querySelector("#kt_sign_in_submit");
            validator = FormValidation.formValidation(form, {
                fields: {
                    email: {
                        validators: {
                            regexp: {
                                regexp: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                                message: "The value is not a valid email address"
                            },
                            notEmpty: {
                                message: "Email address is required"
                            }
                        }
                    },
                    password: {
                        validators: {
                            notEmpty: {
                                message: "The password is required"
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

            submitButton.addEventListener("click", function(event) {
                event.preventDefault();

                validator.validate().then(function(status) {
                    if (status === 'Valid') {
                        submitButton.setAttribute("data-kt-indicator", "on");
                        submitButton.disabled = true;

                        axios.post(form.getAttribute("action"), new FormData(form))
                            .then(function(response) {
                                if (response.data.success) {
                                    var redirectUrl = form.getAttribute("data-kt-redirect-url");
                                    if (redirectUrl) {
                                        window.location.href = redirectUrl;
                                    } else {
                                        window.location.href = '/';  // Default redirect URL
                                    }
                                } else {
                                    Swal.fire({
                                        text: response.data.message || "Sorry, looks like there are some errors detected, please try again.",
                                        icon: "error",
                                        buttonsStyling: false,
                                        confirmButtonText: "Ok, got it!",
                                        customClass: {
                                            confirmButton: "btn btn-primary"
                                        }
                                    });
                                }
                            })
                            .catch(function(error) {
                                Swal.fire({
                                    text: "Sorry, looks like there are some errors detected, please try again.",
                                    icon: "error",
                                    buttonsStyling: false,
                                    confirmButtonText: "Ok, got it!",
                                    customClass: {
                                        confirmButton: "btn btn-primary"
                                    }
                                });
                            })
                            .finally(function() {
                                submitButton.removeAttribute("data-kt-indicator");
                                submitButton.disabled = false;
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
        }
    };
}();
KTUtil.onDOMContentLoaded(function() {
    KTSigninGeneral.init();
});
