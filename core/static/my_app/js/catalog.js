async function AddToCart(name) {
    const response = await fetch("/add_to_cart", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({
            name: name
        })
    })

    const data = await response.json()
    console.log(data)
    const cart = document.querySelector("#in_cart")
    cart.textContent = data.total
}

function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

document.addEventListener('input', async function (event) {
    if (event.target.tagName === 'INPUT' && event.target.type === "checkbox") {
        const category_types = document.querySelectorAll("input[name='category_input']:checked")
        const price_type = document.querySelector("input[name='price_input']:checked")

        let categories = []
        category_types.forEach( (type) => {
            categories.push(type.value.split(" ").join("$"))
        })
        const price = (price_type) ? price_type.value : null
        categories = categories.join("_")
        categories = (categories) ? categories : null

        let url = "/catalog"
        url += (categories) ? `/categories=${categories}` : ''
        if (price) {
            url += (categories) ? `&price=${price}` : `/price=${price}`
        }

        window.location.href = url
    }
})

