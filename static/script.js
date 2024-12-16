function changeYear(year) {
    const currentMonth = new URLSearchParams(window.location.search).get('month') || (new Date().getMonth() + 1);
    window.location.href = `/?year=${year}&month=${currentMonth}`;
}

function changeMonth(month) {
    const currentYear = new URLSearchParams(window.location.search).get('year') || new Date().getFullYear();
    window.location.href = `/?year=${currentYear}&month=${month}`;
}