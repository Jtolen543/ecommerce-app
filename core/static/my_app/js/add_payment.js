async function initialize() {

    csrfToken = getCSRFToken()

    const response = await fetch("/profile/create_setup_intent",{
        method:"POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
    })
    const { public_key, client_secret, link} = await response.json()
    console.log(response)
    console.log(public_key)

    // Initialize Stripe.js with your publishable key
    const stripe = Stripe(public_key);


    // Set up Stripe Elements
    const elements = stripe.elements({
        clientSecret: client_secret
    });

    const options = { mode: 'shipping' };
    const paymentElementOptions = { layout: 'tabs'};

    // Create and mount the Payment Element
    const paymentElement = elements.create("payment", paymentElementOptions);
    const addressElement = elements.create("address", options)
    paymentElement.mount("#payment-element");
    addressElement.mount("#address-element");

    // Handle form submission
    const form = document.getElementById("payment-form");
    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        // Confirm the payment
        const { error } = await stripe.confirmSetup({
            elements,
            confirmParams: {
                return_url: link
            },
        });
        if (error) {
            // Show error message
            const message = document.getElementById("payment-message");
            message.textContent = error.message;
            message.classList.remove("hidden");
        }
    });
}

function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// ------- UI helpers -------

function showMessage(messageText) {
  const messageContainer = document.querySelector("#payment-message");

  messageContainer.classList.remove("hidden");
  messageContainer.textContent = messageText;

  setTimeout(function () {
    messageContainer.classList.add("hidden");
    messageContainer.textContent = "";
  }, 4000);
}

// Show a spinner on payment submission
function setLoading(isLoading) {
  if (isLoading) {
    // Disable the button and show a spinner
    document.querySelector("#submit").disabled = true;
    document.querySelector("#spinner").classList.remove("hidden");
    document.querySelector("#button-text").classList.add("hidden");
  } else {
    document.querySelector("#submit").disabled = false;
    document.querySelector("#spinner").classList.add("hidden");
    document.querySelector("#button-text").classList.remove("hidden");
  }
}

initialize()