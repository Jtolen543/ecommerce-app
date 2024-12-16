let stripeFormId;
let stripeElement;

async function initialize() {
    csrfToken = getCSRFToken()

    const response = await fetch("create_payment_intent",{
        method:"POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
    })
    const data = await response.json()

    // Initialize Stripe.js with your publishable key
    const stripe = Stripe(data.public_key);

    // Set up Stripe Elements
    const elements = stripe.elements({
        clientSecret: data.client_secret
    });

    stripeFormId = data.pi_id
    stripeElement = elements

    let addressElementOptions = {
        mode: 'shipping'
    };

    let paymentElementOptions = {
        layout: 'accordion'
    };

    if (data.address) {
         addressElementOptions = {
            defaultValues: {
                name: data.billingDetails.name,
                address: data.address
            },
            ...addressElementOptions
        };
    }
    console.log(addressElementOptions)

    if (data.billingDetails) {
        paymentElementOptions = {
            defaultValues: {
                billingDetails: data.billingDetails
            },
            ...paymentElementOptions
        }
    }

    // Create and mount the Payment Element
    const paymentElement = elements.create("payment", paymentElementOptions);
    const addressElement = elements.create("address", addressElementOptions)

    addressElement.on('change', (event) => {
        if (event.complete) {
            populateOrder()
            updatePaymentForm()
        }
    })

    paymentElement.mount("#payment-element");
    addressElement.mount("#address-element");

    // Handle form submission
    const form = document.getElementById("payment-form");
    const emailForm = document.getElementById("stripe_email")
    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (re.test(stripe_email.value)) {
            // Confirm the payment
            const { error } = await stripe.confirmPayment({
                elements,
                confirmParams: {
                    return_url: data.success_link,
                    receipt_email: emailForm.value
                },
            });
            if (error) {
                const message = document.getElementById("payment-message");
                message.textContent = error.message;
                message.classList.remove("hidden");
            }
        }
        else {
            const message = document.getElementById("payment-message");
            message.textContent = "Enter a valid email address";
            message.classList.remove("hidden");
        }
    });
}

async function updatePaymentForm() {
    const csrfToken = getCSRFToken()

    console.log(stripeElement)

    let stripe_address_element = await stripeElement.getElement("address")
    let temp = await stripe_address_element.getValue()

    temp = (temp.complete) ? temp.value.address : null

    const response = await fetch("update_payment_intent", {
        method: "POST",
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            pi_id: stripeFormId,
            address: temp
        })
    })
    const data = await response.json()

    document.getElementById("tax").innerText = "$" + (Math.round(data.tax * 100) / 100).toFixed(2);
    document.getElementById("subtotal").innerText = "$" + (Math.round(data.subtotal * 100) / 100).toFixed(2);
    document.getElementById("total").innerText = "$" + (Math.round(data.total * 100) / 100).toFixed(2);
    document.getElementById("shipping").innerText = "$" + (Math.round(data.shipping * 100) / 100).toFixed(2);

}

function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}
async function startElements() {
    await initialize()
    await populateOrder()
}

// Start the checkout session
startElements()

let address_button = document.getElementById("address-button")
let payment_button = document.getElementById("payment-button")
const field_address = document.getElementById("address-select");
const field_payment = document.getElementById("payment-select");

const num_inputs = document.querySelectorAll("input[type='number']")

num_inputs.forEach(input => {
    input.addEventListener('change', async () => {
        await populateOrder(false)
        await updatePaymentForm()
    })
})

async function onCartChange(input, name) {
    const quantity_input = input
    let new_value = parseInt(quantity_input.value)
    const maximum = parseInt(quantity_input.getAttribute("max"))
    const minimum = parseInt(quantity_input.getAttribute("min"))

    let address = document.querySelector("input[name='locations']:checked")
    if (!address) {
        let stripe_address_element = stripeElement.getElement("address")
        let temp = await stripe_address_element.getValue()
        address = temp.value.address
    }
    if (new_value > maximum) {
        quantity_input.value = maximum
        new_value = maximum
    }
    else if (new_value < minimum) {
        quantity_input.value = minimum
        new_value = minimum
    }
    else {
        quantity_input.value = new_value
    }

    input.value = new_value
    const url = `/update_cart/${encodeURIComponent(name)}/${encodeURIComponent(new_value)}`
    const csrfToken = getCSRFToken()

    const data = await fetch(url, {
        method:"POST",
        headers: {
            "Content-type": "applications/json",
            "X-CSRFToken": csrfToken
        }
    })
    .then(response=>response.json())
    document.getElementById("in_cart").innerText = data.cart

    updatePaymentForm()
}

if (address_button) {
    let number;
    address_button.addEventListener("click", async () => {
        if (field_address.classList.contains("expanded")) {
            let empty = true;
            const inputs = field_address.querySelectorAll("input")
            console.log(inputs)
            inputs.forEach( input => {
                if (input.checked) {
                    number = input.value
                    empty = false
                }
            })
            // If field is empty, field will remain open
            if (empty) {
                if (!document.getElementById("address-warning")) {
                    const parent = document.getElementById("address-options")
                    const warning = document.createElement("div")
                    warning.id ="address-warning"
                    warning.classList.add("text-danger", "fw-bold", "fade-in", "expanded")
                    warning.innerText = "Please select a address option"
                    parent.prepend(warning)
                }
            }
            // Logic for closing the field
            else {
                field_address.style.maxHeight = '0'
                field_address.classList.remove("expanded");
                address_button.innerText = "Change";
                if (document.getElementById("address-warning")) document.getElementById("address-warning").remove()

                // API Call
                const data = await fetch(`/get_location_from_id/${number}`, {
                    method: "POST",
                    headers: {
                        'Content-Type': "application/json",
                        "X-CSRFToken": getCSRFToken()
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    document.getElementById("default-name").innerText = data.name,
                    document.getElementById("default-address").innerText = data.address,
                    document.getElementById("default-locale").innerText = data.locale
                })

                populateOrder()

            }
        } else { // Expands the address options and closes any other expanded elements
            if (field_payment.classList.contains("expanded")) {
                payment_button.click()
            }
            field_address.style.maxHeight = field_address.scrollHeight + 'px';
            field_address.classList.add("expanded");

            address_button.innerText = "Close";
        }
    });
} else {
    console.error("Element with ID 'address-button' does not exist");
}

if (payment_button) {
    payment_button.addEventListener("click", async () => {
    let paymentId;
        if (field_payment.classList.contains("expanded")) {
            let empty = true;
            const inputs = field_payment.querySelectorAll("input")
            inputs.forEach( input => {
                if (input.checked) {
                    paymentId = input.value
                    empty = false
                }
            })
            // If unchecked, box will remain open
            if (empty) {
                if (!document.getElementById("payment-warning")) {
                    const parent = document.getElementById("payment-options")
                    const warning = document.createElement("div")
                    warning.id ="payment-warning"
                    warning.classList.add("text-danger", "fw-bold", "fade-in", "expanded")
                    warning.innerText = "Please select a payment option"
                    parent.prepend(warning)
                }
            }
            // Logic for closing the field
            else {
                field_payment.style.maxHeight = '0'
                field_payment.classList.remove("expanded");
                payment_button.innerText = "Change";
                if (document.getElementById("payment-warning")) document.getElementById("payment-warning").remove()
                document.getElementById("payment-table").classList.remove("expanded")

                const response = await fetch("/get_billing_from_id", {
                    method:"POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCSRFToken()
                    },
                    body: JSON.stringify({pm_id: paymentId})
                })
                const data = await response.json()
                document.getElementById("default-payment").innerText = data.card
                document.getElementById("default-payment-name").innerText = data.name
                document.getElementById("default-billing-address").innerText = data.address
                document.getElementById("default-billing-locale").innerText = data.locale

                populateOrder()

            }
        } else { // Expands the payment options and closes any other expanded elements
            if (field_address.classList.contains("expanded")) {
                address_button.click()
            }
            field_payment.style.maxHeight = field_payment.scrollHeight + 'px'
            field_payment.classList.add("expanded");
            payment_button.innerText = "Close";
            document.getElementById("payment-table").style.maxHeight = document.getElementById("payment-table").scrollHeight + 'px'
            document.getElementById("payment-table").classList.add("expanded", "border-bottom")
        }
    });
} else {
    console.error("Element with ID 'payment-button' does not exist");
}

let paymentIntent;
const userStripePayment = document.getElementById('openStripePayment');
userStripePayment.addEventListener('click', () => {
    const payment_container = document.getElementById("payment-container")
    if (payment_container.classList.contains('d-none')) {
        payment_container.classList.remove('d-none')
        if (document.getElementById("express-checkout-btn").classList.contains("reveal")) {
            document.getElementById("express-checkout-btn").classList.remove("reveal")
            document.getElementById("express-checkout-btn").classList.add("disabled")
        }
        field_payment.style.maxHeight = '0'
        field_payment.classList.remove("expanded");
        payment_button.innerText = "Change";
        if (document.getElementById("payment-warning")) document.getElementById("payment-warning").remove()
        document.getElementById("payment-table").classList.remove("expanded")

    } else payment_container.classList.add('d-none')
})


async function populateOrder(update_now=true) {

    console.log(stripeElement)

    let stripe_address_element = stripeElement.getElement("address")
    let temp = await stripe_address_element.getValue()

    const address = document.querySelector("input[name='locations']:checked")
    const payment = document.querySelector("input[name='payments']:checked")
    let data;
    if (address || temp.complete) {
        let response = await fetch("get_order_summary", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({
                "address_id": (temp.complete) ? temp.value.address : address.value,
            })
        })
            data = await response.json()
            if (update_now) {
                document.getElementById("tax").innerText = "$" + (Math.round(data.tax * 100) / 100).toFixed(2);
                document.getElementById("subtotal").innerText = "$" + (Math.round(data.subtotal * 100) / 100).toFixed(2);
                document.getElementById("total").innerText = "$" + (Math.round(data.total * 100) / 100).toFixed(2);
                document.getElementById("shipping").innerText = "$" + (Math.round(data.shipping * 100) / 100).toFixed(2);
            }
    }
    if (address && payment) {
        response = await fetch("/create_express_checkout", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({
                total: Math.round(data.total * 100),
                tax: Math.round(data.tax * 100),
                subtotal: Math.round(data.subtotal * 100),
                shipping: Math.round(data.shipping * 100),
                paymentId: payment.value,
                addressId: address.value
            })
        })

        data = await response.json()
        paymentIntent = data.pi_id
        if (!document.getElementById("express-checkout-btn").classList.contains("reveal")) {
            document.getElementById("express-checkout-btn").classList.add("reveal")
            document.getElementById("express-checkout-btn").classList.remove("disabled")
        }
        document.getElementById("express-checkout-btn").onclick = () => {
            navigateExpress(`finalize_express_checkout/${paymentIntent}`)
        }
    }
}

function navigateExpress (url) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    const currEmail = document.getElementById("stripe_email")
    if (!re.test(currEmail.value)) {
        const message = document.getElementById("express-checkout-warning");
        message.textContent = "Please enter a valid email";
    }
    else {
        window.location.href = url + `/${encodeURIComponent(currEmail.value)}`
    }
}



// ------- UI helpers -------

//function showMessage(messageText) {
//  const messageContainer = document.querySelector("#payment-message");
//
//  messageContainer.classList.remove("hidden");
//  messageContainer.textContent = messageText;
//
//  setTimeout(function () {
//    messageContainer.classList.add("hidden");
//    messageContainer.textContent = "";
//  }, 4000);
//}
//
//// Show a spinner on payment submission
//function setLoading(isLoading) {
//  if (isLoading) {
//    // Disable the button and show a spinner
//    document.querySelector("#submit").disabled = true;
//    document.querySelector("#spinner").classList.remove("hidden");
//    document.querySelector("#button-text").classList.add("hidden");
//  } else {
//    document.querySelector("#submit").disabled = false;
//    document.querySelector("#spinner").classList.add("hidden");
//    document.querySelector("#button-text").classList.remove("hidden");
//  }
//}

