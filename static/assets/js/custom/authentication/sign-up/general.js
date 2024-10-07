"use strict";

var KTSignupGeneral = function() {
    var e, t, r, a, s = function() {
        return a.getScore() > 50;
    };

    return {
        init: function() {
            e = document.querySelector("#kt_sign_up_form");
            t = document.querySelector("#kt_sign_up_submit");
            a = KTPasswordMeter.getInstance(e.querySelector('[data-kt-password-meter="true"]'));

            // Initialize Form Validation
            r = FormValidation.formValidation(e, {
                fields: {
                    "first-name": {
                        validators: {
                            notEmpty: {
                                message: "First Name is required"
                            }
                        }
                    },
                    "last-name": {
                        validators: {
                            notEmpty: {
                                message: "Last Name is required"
                            }
                        }
                    },
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
                            },
                            callback: {
                                message: "Please enter a valid password",
                                callback: function(e) {
                                    if (e.value.length > 0)
                                        return s();
                                }
                            }
                        }
                    },
                    "confirm-password": {
                        validators: {
                            notEmpty: {
                                message: "The password confirmation is required"
                            },
                            identical: {
                                compare: function() {
                                    return e.querySelector('[name="password"]').value;
                                },
                                message: "The password and its confirm are not the same"
                            }
                        }
                    },
                    toc: {
                        validators: {
                            notEmpty: {
                                message: "You must accept the terms and conditions"
                            }
                        }
                    }
                },
                plugins: {
                    trigger: new FormValidation.plugins.Trigger({
                        event: {
                            password: !1
                        }
                    }),
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: ".fv-row",
                        eleInvalidClass: "",
                        eleValidClass: ""
                    })
                }
            });

            t.addEventListener("click", function(a) {
                a.preventDefault();
                r.validate().then(function(r) {
                    if (r === "Valid") {
                        t.setAttribute("data-kt-indicator", "on");
                        t.disabled = true;

                        // Submit form data via AJAX
                        fetch(e.getAttribute("action"), {
                            method: 'POST',
                            body: new FormData(e),
                            headers: {
                                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                            }
                        })
                        .then(response => response.json())
                        .then(data => {
                            t.removeAttribute("data-kt-indicator");
                            t.disabled = false;

                            if (data.success) {
                                // Directly redirect without showing pop-up
                                var redirectUrl = data.redirect_url || '/';
                                location.href = redirectUrl;
                            } else {
                                Swal.fire({
                                    text: data.message || "Sorry, something went wrong. Please try again.",
                                    icon: "error",
                                    buttonsStyling: false,
                                    confirmButtonText: "Ok, got it!",
                                    customClass: {
                                        confirmButton: "btn btn-primary"
                                    }
                                });
                            }
                        })
                        .catch(() => {
                            t.removeAttribute("data-kt-indicator");
                            t.disabled = false;
                            Swal.fire({
                                text: "Sorry, looks like there was an error. Please try again.",
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

            e.querySelector('input[name="password"]').addEventListener("input", function() {
                this.value.length > 0 && r.updateFieldStatus("password", "NotValidated");
            });
        }
    }
}();

KTUtil.onDOMContentLoaded(function() {
    KTSignupGeneral.init();
});