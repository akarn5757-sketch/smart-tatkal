function selectTrain(number, name) {
  const box = document.getElementById("selected");
  const text = document.getElementById("selectedText");
  if (!box || !text) return;
  text.textContent = number + " — " + name + " selected.";
  box.classList.remove("hidden");
  box.scrollIntoView({behavior:"smooth", block:"center"});
}