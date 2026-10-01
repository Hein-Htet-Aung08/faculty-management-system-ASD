const API_BASE_URL = "http://localhost:5002";

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const contentType =
    response.headers.get("content-type") || "";

  let data;

  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    if (
      typeof data === "object" &&
      data !== null
    ) {
      if (data.error) {
        message = data.error;
      } else if (
        Array.isArray(data.errors) &&
        data.errors.length > 0
      ) {
        message = data.errors.join(" ");
      }
    }

    if (
      typeof data === "string" &&
      data.trim()
    ) {
      const parser = new DOMParser();
      const doc = parser.parseFromString(
        data,
        "text/html"
      );

      const text = doc.body.textContent.trim();

      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }

  return data;
}

let staffOptionsPromise = null;


async function getStaffOptions() {
  if (!staffOptionsPromise) {
    staffOptionsPromise =
      apiRequest(
        "/staff-options"
      ).catch(
        error => {
          staffOptionsPromise = null;
          throw error;
        }
      );
  }

  return staffOptionsPromise;
}


function createStaffPicker({
  searchInputId,
  hiddenInputId,
  optionsId,
  selectedId,
  selectedLabelId,
  clearButtonId
}) {
  const searchInput =
    document.getElementById(
      searchInputId
    );

  const hiddenInput =
    document.getElementById(
      hiddenInputId
    );

  const options =
    document.getElementById(
      optionsId
    );

  const selected =
    document.getElementById(
      selectedId
    );

  const selectedLabel =
    document.getElementById(
      selectedLabelId
    );

  const clearButton =
    document.getElementById(
      clearButtonId
    );

  const picker =
    searchInput.closest(
      ".staff-picker"
    );

  let staffMembers = [];


  async function load() {
    if (
      staffMembers.length > 0
    ) {
      return;
    }

    try {
      staffMembers =
        await getStaffOptions();

    } catch (error) {
      staffMembers = [];

      searchInput.placeholder =
        "Unable to load staff";
    }
  }


  function hideOptions() {
    options.hidden = true;
  }


  function getStaffLabel(
    staff
  ) {
    return [
      staff.name,
      staff.position,
      staff.department_name
    ]
      .filter(Boolean)
      .join(" · ");
  }


  function selectStaff(
    staff
  ) {
    hiddenInput.value =
      String(
        staff.staff_id
      );

    searchInput.value =
      staff.name;

    selectedLabel.textContent =
      getStaffLabel(
        staff
      );

    selected.hidden =
      false;

    hideOptions();
  }


  function renderOptions(
    filter = ""
  ) {
    const search =
      filter
        .trim()
        .toLowerCase();

    const matches =
      staffMembers.filter(
        staff => {
          const searchable = [
            staff.name,
            staff.position,
            staff.department_name,
            staff.status
          ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();

          return searchable.includes(
            search
          );
        }
      );

    options.innerHTML = "";

    if (
      matches.length === 0
    ) {
      const empty =
        document.createElement(
          "div"
        );

      empty.className =
        "staff-picker-empty";

      empty.textContent =
        "No matching staff members.";

      options.appendChild(
        empty
      );

      options.hidden =
        false;

      return;
    }

    matches.forEach(
      staff => {
        const button =
          document.createElement(
            "button"
          );

        button.type =
          "button";

        button.className =
          "staff-picker-option";

        const name =
          document.createElement(
            "strong"
          );

        name.textContent =
          staff.name;

        const details =
          document.createElement(
            "span"
          );

        details.textContent = [
          staff.position,
          staff.department_name,
          staff.status
        ]
          .filter(Boolean)
          .join(" · ");

        button.appendChild(
          name
        );

        button.appendChild(
          details
        );

        button.addEventListener(
          "click",
          () => {
            selectStaff(
              staff
            );
          }
        );

        options.appendChild(
          button
        );
      }
    );

    options.hidden =
      false;
  }


  function clear({
    focus = false,
    showOptions = false
  } = {}) {
    hiddenInput.value =
      "";

    searchInput.value =
      "";

    selectedLabel.textContent =
      "";

    selected.hidden =
      true;

    hideOptions();

    if (
      showOptions
    ) {
      renderOptions("");
    }

    if (
      focus
    ) {
      searchInput.focus();
    }
  }


  async function selectById(
    staffId,
    fallbackLabel = ""
  ) {
    if (
      staffId === null ||
      staffId === undefined ||
      staffId === ""
    ) {
      clear();
      return;
    }

    await load();

    const staff =
      staffMembers.find(
        item =>
          String(
            item.staff_id
          ) ===
          String(
            staffId
          )
      );

    if (
      staff
    ) {
      selectStaff(
        staff
      );

      return;
    }

    hiddenInput.value =
      String(
        staffId
      );

    searchInput.value =
      fallbackLabel ||
      `Staff ${staffId}`;

    selectedLabel.textContent =
      searchInput.value;

    selected.hidden =
      false;
  }


  searchInput.addEventListener(
    "focus",
    async () => {
      await load();

      renderOptions(
        searchInput.value
      );
    }
  );


  searchInput.addEventListener(
    "input",
    () => {
      hiddenInput.value =
        "";

      selected.hidden =
        true;

      selectedLabel.textContent =
        "";

      renderOptions(
        searchInput.value
      );
    }
  );


  clearButton.addEventListener(
    "click",
    () => {
      clear({
        focus: true,
        showOptions: true
      });
    }
  );


  document.addEventListener(
    "click",
    event => {
      if (
        !picker.contains(
          event.target
        )
      ) {
        hideOptions();
      }
    }
  );


  load();

  return {
    clear,
    selectById
  };
}