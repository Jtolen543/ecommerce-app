let autocomplete;
let address1Field;
let address2Field;
let postalField;

function initAutocomplete() {
    address1Field = document.querySelector("#main_address");
    address2Field = document.querySelector("#address_details");
    postalField = document.querySelector("#zip_code");

    autocomplete = new google.maps.places.Autocomplete(address1Field, {
        componentRestrictions: { country: ["us", "ca"] },
        fields: ["address_components", "geometry"],
        types: ["address"],
    });
    address1Field.focus();

    autocomplete.addListener("place_changed", fillInAddress);
}

function fillInAddress() {
  const place = autocomplete.getPlace();
  let address1 = "";
  let postcode = "";

  for (const component of place.address_components) {
    const componentType = component.types[0];
    switch (componentType) {
      case "street_number": {
        address1 = `${component.long_name} ${address1}`;
        break;
      }

      case "route": {
        address1 += component.short_name;
        break;
      }

      case "postal_code": {
        postcode = `${component.long_name}${postcode}`;
        break;
      }

      case "postal_code_suffix": {
        postcode = `${postcode}-${component.long_name}`;
        break;
      }
      case "locality":
        document.querySelector("#city").value = component.long_name;
        break;
      case "administrative_area_level_1": {
        document.querySelector("#state").value = component.short_name;
        break;
      }
      case "country":
        document.querySelector("#country").value = component.long_name;
        break;
    }
  }

  address1Field.value = address1;
  postalField.value = postcode;

  address2Field.focus();
}

let map;

async function initMap() {
  const { Map } = await google.maps.importLibrary("maps");
  const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

  map = new Map(document.getElementById("map"), {
    center: { lat: 29.651634, lng: -82.324829 },
    zoom: 12,
    draggable: true,
    mapId: "CONTACT_MAP_ID"
  });

  const marker = new google.maps.marker.AdvancedMarkerElement({
    map,
    position: {lat: 29.651634, lng: -82.324829}
  })

  marker.addListener('click', ({domEvent, latLng}) => {
    map.setCenter(marker.position);
    map.setZoom(12);
  });
}

initMap();

const productContainers = [...document.querySelectorAll('.product-container')];
const nxtBtn = [...document.querySelectorAll('.nxt-btn')];
const preBtn = [...document.querySelectorAll('.pre-btn')];

productContainers.forEach((item, i) => {
    const productCard = item.querySelector('.product-card')
    const productCardWidth = productCard.getBoundingClientRect().width;

    nxtBtn[i].addEventListener('click', () => {
        item.scrollLeft += productCardWidth;
    })

    preBtn[i].addEventListener('click', () => {
        item.scrollLeft -= productCardWidth;
    })
})

window.addEventListener('load', initAutocomplete)

async function addProduct(button, name) {
    const quantity_input = button.previousElementSibling
    const new_value = parseInt(quantity_input.value) + 1
    const maximum = quantity_input.getAttribute("max")

    const address = document.querySelector("input[name='locations']:checked")
    if (address) loc = address.value

    if (new_value <= maximum) {
        quantity_input.value = new_value
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

    document.getElementById("tax").innerText = "$" + (Math.round(data.tax * 100) / 100).toFixed(2);
    document.getElementById("subtotal").innerText = "$" + (Math.round(data.subtotal * 100) / 100).toFixed(2);
    document.getElementById("total").innerText = "$" + (Math.round(data.total * 100) / 100).toFixed(2);
    document.getElementById("shipping").innerText = "$" + (Math.round(data.shipping * 100) / 100).toFixed(2);
    document.getElementById("in_cart").innerText = data.cart

    }
    else {
        console.log("Element is too large!")
    }
}

async function subtractProduct(button, name) {
    const quantity_input = button.nextElementSibling
    const new_value = parseInt(quantity_input.value) - 1
    const minimum = quantity_input.getAttribute("minimum")

    const address = document.querySelector("input[name='locations']:checked")
    if (address) loc = address.value

    if (new_value > minimum) {
        quantity_input.value = new_value
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

    document.getElementById("tax").innerText = "$" + (Math.round(data.tax * 100) / 100).toFixed(2);
    document.getElementById("subtotal").innerText = "$" + (Math.round(data.subtotal * 100) / 100).toFixed(2);
    document.getElementById("total").innerText = "$" + (Math.round(data.total * 100) / 100).toFixed(2);
    document.getElementById("shipping").innerText = "$" + (Math.round(data.shipping * 100) / 100).toFixed(2);
    document.getElementById("in_cart").innerText = data.cart


    }
    else {
        console.log("Element is too small!")
    }
}

async function onAmountChange(input, name) {
    const quantity_input = input
    let new_value = parseInt(quantity_input.value)
    const maximum = parseInt(quantity_input.getAttribute("max"))
    const minimum = parseInt(quantity_input.getAttribute("min"))

    const address = document.querySelector("input[name='locations']:checked")
    if (address) loc = address.value

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

    document.getElementById("tax").innerText = "$" + (Math.round(data.tax * 100) / 100).toFixed(2);
    document.getElementById("subtotal").innerText = "$" + (Math.round(data.subtotal * 100) / 100).toFixed(2);
    document.getElementById("total").innerText = "$" + (Math.round(data.total * 100) / 100).toFixed(2);
    document.getElementById("shipping").innerText = "$" + (Math.round(data.shipping * 100) / 100).toFixed(2);
    document.getElementById("in_cart").innerText = data.cart
}

function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('deleteAccountForm');
    const password = document.querySelector("#currentPassword")
    console.log(password.value)

    form.addEventListener('submit', async function(event) {
        event.preventDefault();

        // Fetches data from server
        const response = await fetch('validate_user_delete', {
          method: 'post',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
          },
          body: JSON.stringify({
            password: password.value
          })
        })

        const data = await response.json()

        console.log(data)

        // Verifies data is correct
        const validation = document.querySelector("#passwordError")
        if (data.validated) {
            // Show confirmation modal
            validation.textContent = ''
            const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
            modal.show();
        } else {
            validation.textContent = "Password is incorrect, please try again"
        }
    });

});