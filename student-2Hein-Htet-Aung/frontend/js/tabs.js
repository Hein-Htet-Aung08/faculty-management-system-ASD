const tabButtons = document.querySelectorAll(".tab-button");
const tabSections = document.querySelectorAll("main .panel-section[id]");

tabButtons.forEach(button => {
  button.addEventListener("click", () => {
    const targetId = button.dataset.tab;

    tabButtons.forEach(tab => {
      tab.classList.remove("active");
    });

    tabSections.forEach(section => {
      section.hidden = section.id !== targetId;
    });

    button.classList.add("active");
  });
});