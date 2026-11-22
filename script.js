const searchForm = document.querySelector("#vehicle-search");
const makeFilter = document.querySelector("#make-filter");
const modelFilter = document.querySelector("#model-filter");
const yearFilter = document.querySelector("#year-filter");
const priceFilter = document.querySelector("#price-filter");
const vehicleCards = [...document.querySelectorAll(".car-card")];
const noResults = document.querySelector("#no-results");
const conditionTabs = [...document.querySelectorAll(".search-tab")];
const menuToggle = document.querySelector(".menu-toggle");
const mainNav = document.querySelector(".main-nav");
let selectedCondition = "all";

function filterVehicles() {
  let visibleCount = 0;
  vehicleCards.forEach((card) => {
    const matches =
      (!makeFilter.value || card.dataset.make === makeFilter.value) &&
      (!modelFilter.value || card.dataset.model === modelFilter.value) &&
      (!yearFilter.value || card.dataset.year === yearFilter.value) &&
      (!priceFilter.value || Number(card.dataset.price) <= Number(priceFilter.value)) &&
      (selectedCondition === "all" || card.dataset.condition === selectedCondition);
    card.hidden = !matches;
    if (matches) visibleCount += 1;
  });
  noResults.hidden = visibleCount > 0;
}

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  filterVehicles();
  document.querySelector("#inventory").scrollIntoView({ behavior: "smooth" });
});

conditionTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    conditionTabs.forEach((item) => item.classList.toggle("selected", item === tab));
    selectedCondition = tab.dataset.condition;
    filterVehicles();
  });
});

document.querySelectorAll(".favorite").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
    button.classList.toggle("saved");
    button.textContent = button.classList.contains("saved") ? "♥" : "♡";
    button.setAttribute("aria-pressed", String(button.classList.contains("saved")));
  });
});

menuToggle.addEventListener("click", () => {
  const isOpen = mainNav.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", String(isOpen));
  menuToggle.setAttribute("aria-label", isOpen ? "Close menu" : "Open menu");
});

mainNav.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    mainNav.classList.remove("open");
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "Open menu");
  });
});
