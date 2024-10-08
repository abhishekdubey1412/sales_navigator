"use strict";

var KTAccountSettingsSigninMethods = function() {
    var t, e, n, o, i, s, r, a, l, d, m, c;

    var toggleEmailEdit = function() {
        e.classList.toggle("d-none");
        s.classList.toggle("d-none");
        n.classList.toggle("d-none");
    };

    var togglePasswordEdit = function() {
        o.classList.toggle("d-none");
        a.classList.toggle("d-none");
        i.classList.toggle("d-none");
    };

    var submitEmailForm = function(e) {
        e.preventDefault();

        var formData = new FormData(t);
        fetch('/update-email/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken') // Ensure CSRF token is included
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                swal.fire({
                    text: data.message,
                    icon: "success",
                    buttonsStyling: !1,
                    confirmButtonText: "Ok, got it!",
                    customClass: {
                        confirmButton: "btn font-weight-bold btn-light-primary"
                    }
                }).then(() => {
                    // Refresh the page after success
                    location.reload();
                });
            } else {
                swal.fire({
                    text: data.message,
                    icon: "error",
                    buttonsStyling: !1,
                    confirmButtonText: "Ok, got it!",
                    customClass: {
                        confirmButton: "btn font-weight-bold btn-light-primary"
                    }
                });
            }
        });
    };

    var submitPasswordForm = function(e) {
        e.preventDefault();

        var formData = new FormData(m);
        fetch('/change-password/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken') // Ensure CSRF token is included
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                swal.fire({
                    text: data.message,
                    icon: "success",
                    buttonsStyling: !1,
                    confirmButtonText: "Ok, got it!",
                    customClass: {
                        confirmButton: "btn font-weight-bold btn-light-primary"
                    }
                }).then(() => {
                    // Refresh the page after success
                    location.reload();
                });
            } else {
                swal.fire({
                    text: data.message,
                    icon: "error",
                    buttonsStyling: !1,
                    confirmButtonText: "Ok, got it!",
                    customClass: {
                        confirmButton: "btn font-weight-bold btn-light-primary"
                    }
                });
            }
        });
    };

    // Helper function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    return {
        init: function() {
            t = document.getElementById("kt_signin_change_email");
            e = document.getElementById("kt_signin_email");
            n = document.getElementById("kt_signin_email_edit");
            o = document.getElementById("kt_signin_password");
            i = document.getElementById("kt_signin_password_edit");
            s = document.getElementById("kt_signin_email_button");
            r = document.getElementById("kt_signin_cancel");
            a = document.getElementById("kt_signin_password_button");
            l = document.getElementById("kt_password_cancel");
            m = document.getElementById("kt_signin_change_password");
            c = document.getElementById("kt_password_submit");

            s.querySelector("button").addEventListener("click", toggleEmailEdit);
            r.addEventListener("click", toggleEmailEdit);
            a.querySelector("button").addEventListener("click", togglePasswordEdit);
            l.addEventListener("click", togglePasswordEdit);

            if (t) {
                t.querySelector("#kt_signin_submit").addEventListener("click", submitEmailForm);
            }

            if (m) {
                c.addEventListener("click", submitPasswordForm);
            }
        }
    }
}();

KTUtil.onDOMContentLoaded(function() {
    KTAccountSettingsSigninMethods.init();
});
