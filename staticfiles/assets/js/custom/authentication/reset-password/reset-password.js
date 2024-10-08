"use strict";

var KTAuthResetPassword = function() {
    var t, e, r;

    return {
        init: function() {
            t = document.querySelector("#kt_password_reset_form"),
            e = document.querySelector("#kt_password_reset_submit"),
            r = FormValidation.formValidation(t, {
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
                    phone: {
                        validators: {
                            notEmpty: {
                                message: "Phone number is required"
                            },
                            regexp: {
                                regexp: /^\d{10}$/,
                                message: "Phone number must be exactly 10 digits"
                            }
                        }
                    }
                },
                plugins: {
                    trigger: new FormValidation.plugins.Trigger,
                    bootstrap: new FormValidation.plugins.Bootstrap5({
                        rowSelector: ".fv-row",
                        eleInvalidClass: "",
                        eleValidClass: ""
                    })
                }
            }),
            e.addEventListener("click", function(i) {
                i.preventDefault();
                r.validate().then(function(result) {
                    if (result === "Valid") {
                        e.setAttribute("data-kt-indicator", "on");
                        e.disabled = true;

                        axios.post(t.getAttribute("action"), new FormData(t))
                        .then(function(response) {
                            if (response.data.success) {
                                t.reset();
                                Swal.fire({
                                    text: "We have sent a password reset link to your email.",
                                    icon: "success",
                                    buttonsStyling: false,
                                    confirmButtonText: "Ok, got it!",
                                    customClass: {
                                        confirmButton: "btn btn-primary"
                                    }
                                }).then(function(confirm) {
                                    if (confirm.isConfirmed) {
                                        var redirectUrl = response.data.redirect_url;
                                        if (redirectUrl) {
                                            location.href = redirectUrl;
                                        }
                                    }
                                });
                            } else {
                                Swal.fire({
                                    text: response.data.message,
                                    icon: "error",
                                    buttonsStyling: false,
                                    confirmButtonText: "Ok, got it!",
                                    customClass: {
                                        confirmButton: "btn btn-primary"
                                    }
                                });
                            }
                        })
                        .catch(function() {
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
                            e.removeAttribute("data-kt-indicator");
                            e.disabled = false;
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
    }
}();

KTUtil.onDOMContentLoaded(function() {
    KTAuthResetPassword.init();
});
