"use strict"; 
var KTAuthNewPassword = function() {
    var form, submitButton, passwordMeter, validator;

    var isPasswordValid = function() {
        return passwordMeter.getScore() > 50;
    };

    return {
        init: function() {
            form = document.querySelector("#kt_new_password_form");
            submitButton = document.querySelector("#kt_new_password_submit");
            passwordMeter = KTPasswordMeter.getInstance(form.querySelector('[data-kt-password-meter="true"]'));
            validator = FormValidation.formValidation(form, {
                fields: {
                    password: {
                        validators: {
                            notEmpty: { message: "The password is required" },
                            callback: {
                                message: "Please enter a valid password",
                                callback: function(input) {
                                    if (input.value.length > 0) return isPasswordValid();
                                }
                            }
                        }
                    },
                    "confirm-password": {
                        validators: {
                            notEmpty: { message: "The password confirmation is required" },
                            identical: {
                                compare: function() {
                                    return form.querySelector('[name="password"]').value;
                                },
                                message: "The password and its confirm are not the same"
                            }
                        }
                    },
                    toc: {
                        validators: {
                            notEmpty: { message: "You must accept the terms and conditions" }
                        }
                    }
                },
                plugins: {
                    trigger: new FormValidation.plugins.Trigger({ event: { password: false } }),
                    bootstrap: new FormValidation.plugins.Bootstrap5({ rowSelector: ".fv-row", eleInvalidClass: "", eleValidClass: "" })
                }
            });

            submitButton.addEventListener("click", function(e) {
                e.preventDefault();
                validator.revalidateField("password");
                validator.validate().then(function(status) {
                    if (status == "Valid") {
                        submitButton.setAttribute("data-kt-indicator", "on");
                        submitButton.disabled = true;

                        // Submit the form using fetch
                        fetch(form.getAttribute("action"), {
                            method: "POST",
                            headers: {
                                'X-CSRFToken': getCookie('csrftoken'), // Get CSRF token for Django
                                'Content-Type': 'application/x-www-form-urlencoded'
                            },
                            body: new URLSearchParams(new FormData(form))
                        })
                        .then(response => response.json())
                        .then(data => {
                            submitButton.removeAttribute("data-kt-indicator");
                            submitButton.disabled = false;
                            if (data.success) {
                                window.location.href = data.redirect_url || "/";
                            } else {
                                Swal.fire({ text: data.message || "An error occurred.", icon: "error", confirmButtonText: "Ok, got it!" });
                            }
                        })
                        .catch(error => {
                            submitButton.removeAttribute("data-kt-indicator");
                            submitButton.disabled = false;
                            Swal.fire({ text: "Sorry, looks like there are some errors detected, please try again.", icon: "error", confirmButtonText: "Ok, got it!" });
                        });
                    } else {
                        Swal.fire({ text: "Sorry, looks like there are some errors detected, please try again.", icon: "error", confirmButtonText: "Ok, got it!" });
                    }
                });
            });
        }
    };
}();

KTUtil.onDOMContentLoaded(function() {
    KTAuthNewPassword.init();
});

// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}