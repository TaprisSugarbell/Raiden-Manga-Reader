function SearchChapters() {
    const searchTerm = document.getElementById("search_box").value.trim();
    const chapters = document.getElementsByClassName("book");

    for (const chapter of chapters) {
        const titleElement = chapter.querySelector(".book-name");
        const titleText = (titleElement.textContent || titleElement.innerText).trim();

        // Extraer el número ignorando texto (ej: "Chapter 100" → 100)
        const chapterNumber = titleText.match(/\d+/)?.[0] || "";

        // Comparación exacta del número (si buscas "100" no mostrará "1000")
        chapter.style.display = chapterNumber === searchTerm ? "" : "none";
    }
}
