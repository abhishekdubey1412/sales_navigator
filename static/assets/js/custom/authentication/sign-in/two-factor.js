"use strict";

var KTSigninTwoFactor = function() {
    var t, e;

    return {
        init: function() {
            t = document.querySelector("#kt_sing_in_two_factor_form");
            e = document.querySelector("#kt_sing_in_two_factor_submit");

            e.addEventListener("click", function(n) {
                n.preventDefault();

                var allFilled = true;
                var otpInputs = [].slice.call(t.querySelectorAll('input[maxlength="1"]'));

                // Check if all OTP fields are filled
                otpInputs.forEach(function(input) {
                    if (input.value === "" || input.value.length === 0) {
                        allFilled = false;
                    }
                });

                if (allFilled) {
                    e.setAttribute("data-kt-indicator", "on");
                    e.disabled = true;

                    // Collect OTP values
                    var otpValues = otpInputs.map(function(input) {
                        return input.value;
                    }).join('');

                    // Send OTP to server via AJAX
                    fetch(t.action, { // Use form action URL
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value
                        },
                        body: new URLSearchParams({
                            'code_1': otpValues[0],
                            'code_2': otpValues[1],
                            'code_3': otpValues[2],
                            'code_4': otpValues[3],
                            'code_5': otpValues[4],
                            'code_6': otpValues[5]
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        e.removeAttribute("data-kt-indicator");
                        e.disabled = false;

                        if (data.success) {
                            // Check if a redirect URL is present
                            if (data.redirect_url) {
                                // Redirect directly if a URL is provided
                                location.href = data.redirect_url;
                            } else {
                                // Show success message if no redirect URL
                                Swal.fire({
                                    text: "You have been successfully verified!",
                                    icon: "success",
                                    buttonsStyling: false,
                                    confirmButtonText: "Ok, got it!",
                                    customClass: {
                                        confirmButton: "btn btn-primary"
                                    }
                                }).then(function(result) {
                                    if (result.isConfirmed) {
                                        otpInputs.forEach(function(input) {
                                            input.value = "";
                                        });
                                    }
                                });
                            }
                        } else {
                            Swal.fire({
                                text: data.message || "An error occurred. Please try again.",
                                icon: "error",
                                buttonsStyling: false,
                                confirmButtonText: "Ok, got it!",
                                customClass: {
                                    confirmButton: "btn fw-bold btn-light-primary"
                                }
                            }).then(function() {
                                KTUtil.scrollTop();
                            });
                        }
                    })
                    .catch(error => {
                        e.removeAttribute("data-kt-indicator");
                        e.disabled = false;
                        Swal.fire({
                            text: "Failed to process your request. Please try again.",
                            icon: "error",
                            buttonsStyling: false,
                            confirmButtonText: "Ok, got it!",
                            customClass: {
                                confirmButton: "btn fw-bold btn-light-primary"
                            }
                        });
                    });
                } else {
                    Swal.fire({
                        text: "Please enter valid security code and try again.",
                        icon: "error",
                        buttonsStyling: false,
                        confirmButtonText: "Ok, got it!",
                        customClass: {
                            confirmButton: "btn fw-bold btn-light-primary"
                        }
                    }).then(function() {
                        KTUtil.scrollTop();
                    });
                }
            });

            var n = t.querySelector("[name=code_1]"),
                i = t.querySelector("[name=code_2]"),
                o = t.querySelector("[name=code_3]"),
                u = t.querySelector("[name=code_4]"),
                r = t.querySelector("[name=code_5]"),
                c = t.querySelector("[name=code_6]");

            n.focus();

            n.addEventListener("keyup", function() {
                if (this.value.length === 1) i.focus();
            });

            i.addEventListener("keyup", function() {
                if (this.value.length === 1) o.focus();
            });

            o.addEventListener("keyup", function() {
                if (this.value.length === 1) u.focus();
            });

            u.addEventListener("keyup", function() {
                if (this.value.length === 1) r.focus();
            });

            r.addEventListener("keyup", function() {
                if (this.value.length === 1) c.focus();
            });

            c.addEventListener("keyup", function() {
                if (this.value.length === 1) c.blur();
            });
        }
    };
}();

KTUtil.onDOMContentLoaded(function() {
    KTSigninTwoFactor.init();
});
