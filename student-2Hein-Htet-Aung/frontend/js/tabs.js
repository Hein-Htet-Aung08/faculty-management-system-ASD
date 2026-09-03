const tabButtons = document.querySelectorAll(".tab-button");
const tabSections = document.querySelectorAll("main .panel-section[id]");

tabButtons.forEach(button => {
  button.addEventListener("click", async () => {
    const targetId = button.dataset.tab;

    tabButtons.forEach(tab => {
      tab.classList.remove("active");
    });

    tabSections.forEach(section => {
      section.hidden =
        section.id !== targetId;
    });

    button.classList.add("active");

    if (
      targetId === "ai-recommendations" &&
      typeof loadNeedsAssignmentAllocations === "function"
    ) {
      await loadNeedsAssignmentAllocations();
    }

    if (
      targetId === "allocations" &&
      typeof loadAllocations === "function"
    ) {
      await loadAllocations();
    }
  });
});