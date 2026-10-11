// ============================================================================
// Period pickers — turn the Week / Month / Quarter / Year boxes into dropdowns
// so reps can't save the same period under two spellings ("Oct 2026" vs
// "October 2026"). Each dropdown saves EXACTLY the format the pages already
// use, so existing records keep loading:
//   Weekly tracker:  week_number 1-5,  month "October 2026"
//   Monthly review:  month_year "2026-10"
//   Quarterly review: quarter_year "2026-Q4"
//   Yearly review:   year 2026
// Choices run from January of last year through December of next year, and
// each dropdown starts on the current period.
// ============================================================================

(function () {
  const MONTHS = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];
  const now = new Date();
  const thisYear = now.getFullYear();
  const years = [thisYear - 1, thisYear, thisYear + 1];

  function fill(select, options, selectedValue) {
    select.innerHTML = "";
    options.forEach(({ value, label }) => {
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = label;
      if (String(value) === String(selectedValue)) opt.selected = true;
      select.appendChild(opt);
    });
  }

  // Swap an <input> for a <select> with the same id, so the page's own code
  // (which reads .value by id) keeps working unchanged.
  function toSelect(id) {
    const input = document.getElementById(id);
    if (!input) return null;
    const select = document.createElement("select");
    select.id = id;
    input.replaceWith(select);
    return select;
  }

  // Week 1 = days 1-7 of the month, week 2 = days 8-14, and so on (up to 5).
  const sel = toSelect("week-number");
  if (sel) {
    fill(sel, [1, 2, 3, 4, 5].map((n) => ({ value: n, label: "Week " + n })),
      Math.ceil(now.getDate() / 7));
  }

  const weekMonth = toSelect("week-month");
  if (weekMonth) {
    const opts = [];
    years.forEach((y) => MONTHS.forEach((m) => opts.push({ value: `${m} ${y}`, label: `${m} ${y}` })));
    fill(weekMonth, opts, `${MONTHS[now.getMonth()]} ${thisYear}`);
  }

  const monthYear = toSelect("month-year");
  if (monthYear) {
    const opts = [];
    years.forEach((y) => MONTHS.forEach((m, i) => {
      opts.push({ value: `${y}-${String(i + 1).padStart(2, "0")}`, label: `${m} ${y}` });
    }));
    fill(monthYear, opts, `${thisYear}-${String(now.getMonth() + 1).padStart(2, "0")}`);
  }

  const quarterYear = toSelect("quarter-year");
  if (quarterYear) {
    const ranges = ["Jan–Mar", "Apr–Jun", "Jul–Sep", "Oct–Dec"];
    const opts = [];
    years.forEach((y) => [1, 2, 3, 4].forEach((q) => {
      opts.push({ value: `${y}-Q${q}`, label: `Q${q} ${y} (${ranges[q - 1]})` });
    }));
    fill(quarterYear, opts, `${thisYear}-Q${Math.floor(now.getMonth() / 3) + 1}`);
  }

  const year = toSelect("year");
  if (year) {
    fill(year, years.map((y) => ({ value: y, label: String(y) })), thisYear);
  }
})();
