const alltable = document.getElementById("newreimbursements");
const allheadercells = alltable.querySelectorAll("th");
const allRows = Array.from(alltable.querySelectorAll("tbody tr"));
const tbody = alltable.getElementsByTagName("tbody");
const totalRow = tbody[0].children.length;
const itemsPerPage = 7;
let currentPage = 1;

function addTableSrNo() {
    for (let i = 0; i < totalRow; i++) {
        tbody[0].children[i].firstElementChild.innerText = i + 1;
    }
}

addTableSrNo();
let filteredRows = [];
function showPage(page) {
    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const rows = filteredRows.slice(startIndex, endIndex);
    // Hide all rows
    allRows.forEach((row) => (row.style.display = "none"));
    // Show rows for current page
    rows.forEach((row) => (row.style.display = ""));
}
function updatePaginationButtons() {
    const pageButtonsContainer = document.getElementById("page-buttons");
    const buttons = pageButtonsContainer.querySelectorAll("button");
    buttons.forEach((button) => {
        button.classList.remove("active");
        if (Number(button.textContent) === currentPage) {
            button.classList.add("active");
        }
    });

    const prevButton = pageButtonsContainer.querySelector("button:first-child");
    const nextButton = pageButtonsContainer.querySelector(".next-button");

    prevButton.disabled = currentPage === 1;
    nextButton.disabled = currentPage === Math.ceil(filteredRows.length / itemsPerPage);
}

function applySearchFilter(searchValue) {
    filteredRows = allRows.filter((row) => {
        const cellValue1 = row.cells[2].innerText;
        const cellValue2 = row.cells[3].innerText.toLowerCase();
        return cellValue1.includes(searchValue) || cellValue2.includes(searchValue);
    });
}

function renderPageButtons() {
    const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
    const pageButtonsContainer = document.getElementById("page-buttons");
    pageButtonsContainer.innerHTML = "";

    // Add previous page button
    const prevButton = document.createElement("button");
    prevButton.innerHTML = '<i class="fa fa-angle-left"></i>';

    // Add next page button
    const nextButton = document.createElement("button");
    nextButton.innerHTML = '<i class="fa fa-angle-right"></i>';

    // Angle bracket for left arrow
    prevButton.addEventListener("click", function () {
        if (currentPage > 1) {
            currentPage--;
            showPage(currentPage);
            updatePaginationButtons();
        }
    });
    pageButtonsContainer.appendChild(prevButton);

    // Add page buttons
    for (let i = 1; i <= totalPages; i++) {
        const button = document.createElement("button");
        button.textContent = i;
        if (i === currentPage) {
            button.classList.add("active");
        }

        button.addEventListener("click", function () {
            currentPage = i;
            showPage(currentPage);
            updatePaginationButtons();
        });

        pageButtonsContainer.appendChild(button);
    }

    // Angular bracket for right arrow
    nextButton.classList.add("next-button");
    nextButton.addEventListener("click", function () {
        if (currentPage < totalPages) {
            currentPage++;
            showPage(currentPage);
            updatePaginationButtons();
        }
    });
    pageButtonsContainer.appendChild(nextButton);

    updatePaginationButtons();
}
function compareCellValues(a, b, columnIndex) {
    const aCellValue = a.cells[columnIndex].textContent.trim().replace(/,/g, "");
    const bCellValue = b.cells[columnIndex].textContent.trim().replace(/,/g, "");
    const aNumber = parseFloat(aCellValue);
    const bNumber = parseFloat(bCellValue);

    if (!isNaN(aNumber) && !isNaN(bNumber)) {
        return aNumber - bNumber;
    }
    return aCellValue.localeCompare(bCellValue);
}

allheadercells.forEach(function (th) {
    // Default sort order
    let sortOrder = "asc";
    th.addEventListener("click", function () {
        const columnIndex = th.cellIndex;
        allRows.sort(function (a, b) {
            let comparison = compareCellValues(a, b, columnIndex);

            if (sortOrder === "desc") {
                comparison *= -1;
            }
            return comparison;
        });

        sortOrder = sortOrder === "asc" ? "desc" : "asc";
        allRows.forEach((row) => {
            alltable.tBodies[0].appendChild(row);
        });
        allRows.forEach((row, index) => {
            const firstCell = row.cells[0];
            firstCell.innerText = index + 1;
        });
        currentPage = 1;
        showPage(currentPage);
        renderPageButtons();
    });
});

const searchInputText = document.getElementById("search-text");
const searchClearText = document.getElementById("search-text-clear");
searchClearText.style.display = "none";

function handleSearch() {
    var searchValue = searchInputText.value;

    if (typeof searchValue === "string") {
        searchValue = searchValue.toLowerCase();
    }

    if (searchValue) {
        applySearchFilter(searchValue);
        currentPage = 1;
        showPage(currentPage);
        renderPageButtons();
    } else {
        filteredRows = allRows;
        currentPage = 1;
        showPage(currentPage);
        renderPageButtons();
    }

    searchClearText.style.display = searchValue ? "block" : "none";
}

searchInputText.addEventListener("input", handleSearch);

searchClearText.addEventListener("click", function () {
    searchInputText.value = "";
    handleSearch();
});

document.addEventListener("click", function (event) {
    if (event.target !== searchInputText && event.target !== searchClearText) {
        searchClearText.style.display = searchInputText.value ? "block" : "none";
    }
});

// Initial setup
filteredRows = allRows;
showPage(currentPage);
renderPageButtons();
