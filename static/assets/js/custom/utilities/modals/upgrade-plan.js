"use strict";
var KTModalUpgradePlan = function() {
    var t, n, e, a, i = function(n) {
        [].slice.call(t.querySelectorAll("[data-kt-plan-price-month]")).map((function(t) {
            var e = t.getAttribute("data-kt-plan-price-month"),
                a = t.getAttribute("data-kt-plan-price-annual");
            "month" === n ? t.innerHTML = e : "annual" === n && (t.innerHTML = a)
        }));
    };
    
    return {
        init: function() {
            (t = document.querySelector("#kt_modal_upgrade_plan")) && (n = t.querySelector('[data-kt-plan="month"]'),
            e = t.querySelector('[data-kt-plan="annual"]'),
            a = document.querySelector("#kt_modal_upgrade_plan_btn"),
            n.addEventListener("click", (function(t) {
                t.preventDefault(),
                n.classList.add("active"),
                e.classList.remove("active"),
                i("month")
            })),
            e.addEventListener("click", (function(t) {
                t.preventDefault(),
                n.classList.remove("active"),
                e.classList.add("active"),
                i("annual")
            })),
            a && a.addEventListener("click", (function(n) {
                n.preventDefault();
                var e = this;
                swal.fire({
                    text: "Are you sure you would like to upgrade to selected plan?",
                    icon: "warning",
                    buttonsStyling: !1,
                    showDenyButton: !0,
                    confirmButtonText: "Yes",
                    denyButtonText: "No",
                    customClass: {
                        confirmButton: "btn btn-primary",
                        denyButton: "btn btn-light-danger"
                    }
                }).then((n => {
                    if (n.isConfirmed) {
                        var selectedPlan = t.querySelector('.nav-group-outline .active').getAttribute('data-kt-plan');
                        var Package = t.querySelector('.nav-link.active').getAttribute('data-bs-target');

                        e.setAttribute("data-kt-indicator", "on"),
                        e.disabled = !0;

                        // Sending the data via POST
                        fetch('/upgrade-plan/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCookie('csrftoken')  // Ensure you have CSRF token if using Django
                            },
                            body: JSON.stringify({
                                selectedPlan: selectedPlan,
                                Package: Package.split('#kt_upgrade_plan_')[1]
                            })
                        }).then(response => {
                            if (response.ok) {
                                return response.json();
                            }
                            throw new Error('Network response was not ok.');
                        }).then(data => {
                            Swal.fire({
                                text: "Your subscription plan has been successfully upgraded",
                                icon: "success",
                                confirmButtonText: "Ok",
                                buttonsStyling: !1,
                                customClass: {
                                    confirmButton: "btn btn-light-primary"
                                }
                            }).then(() => {
                                bootstrap.Modal.getInstance(t).hide();
                                window.location.reload()
                            });
                        }).catch(error => {
                            Swal.fire({
                                text: "There was an error upgrading your plan.",
                                icon: "error",
                                confirmButtonText: "Ok",
                                buttonsStyling: !1,
                                customClass: {
                                    confirmButton: "btn btn-light-danger"
                                }
                            });
                        });
                    }
                }));
            })),
            i());
        }
    }
}();

KTUtil.onDOMContentLoaded((function() {
    KTModalUpgradePlan.init();
}));

// Helper function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Check if this cookie string begins with the name we want
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
