// static/mapping_tool/js/board_creator_v2.js
document.addEventListener('DOMContentLoaded', () => {
    // Sekcje kroków
    const step1MapGridSelection = document.getElementById('step-1-map-grid-selection');
    const step2WaystonePlacement = document.getElementById('step-2-waystone-placement');

    // Elementy DOM
    const boardNameInput = document.getElementById('boardName');
    const mapSelect = document.getElementById('mapSelect');
    const gridRowsInput = document.getElementById('gridRows');
    const gridColsInput = document.getElementById('gridCols');
    let mapBgImg = document.getElementById('map-background-img');
    const canvas = document.getElementById('grid-overlay-canvas');
    const ctx = canvas.getContext('2d');
    const colorPaletteContainer = document.querySelector('.color-palette');
    const validationMessageEl = document.getElementById('validation-message');

    // Przyciski
    const confirmGridButton = document.getElementById('confirmGridButton');
    const saveBoardButton = document.getElementById('saveBoardButton');
    const resetToStep1Button = document.getElementById('resetToStep1Button');

    // Dane z szablonu
    const WAYSTONE_COLORS_DATA = JSON.parse(document.getElementById('waystone-colors-data').textContent);
    const API_BOARDS_ENDPOINT = document.getElementById('api-boards-endpoint').textContent.trim();
    const initialMapIdFromDjango = document.getElementById('initial-map-id-data').textContent.trim();


    // Stan aplikacji
    let currentMapData = null; // { id, imageUrl, naturalWidth, naturalHeight }
    let grid = { rows: 0, cols: 0, cellWidth: 0, cellHeight: 0 };
    let waystones = [];
    let selectedColor = null;
    let isGridConfirmed = false;

    // --- Inicjalizacja Listenerów ---
    mapSelect.addEventListener('change', handleMapChange);
    gridRowsInput.addEventListener('input', handleGridDimensionChange);
    gridColsInput.addEventListener('input', handleGridDimensionChange);
    confirmGridButton.addEventListener('click', confirmGridAndProceedToStep2);
    colorPaletteContainer.addEventListener('click', handleColorSelection);
    canvas.addEventListener('click', handleCanvasClick);
    resetToStep1Button.addEventListener('click', resetToStep1);
    saveBoardButton.addEventListener('click', saveBoard);

    // --- Inicjalizacja UI ---
    function initializeUI() {
        console.log("Initializing UI...");
        if (initialMapIdFromDjango) {
            mapSelect.value = initialMapIdFromDjango;
        }
        handleMapChange(); // Załaduj mapę, jeśli jest wybrana
        // updateGridPreview(); // Narysuj siatkę, jeśli wymiary są zdefiniowane
        // validateBoard(); // Ustaw stan przycisku zapisu
    }


    function handleMapChange() {
        console.log("Map selection changed.");
        const selectedOption = mapSelect.options[mapSelect.selectedIndex];

        // Jeśli wybrano opcję "-- Wybierz mapę --" (która ma pustą wartość)
        if (!selectedOption || !selectedOption.value) {
            console.log("No map selected or placeholder selected.");
            mapBgImg.style.display = 'none';
            mapBgImg.src = '#'; // Ustaw na coś neutralnego, aby nie triggerować onerror dla poprzedniego src
            currentMapData = null;
            clearCanvasAndHide(); // Wyczyść i ukryj canvas
            // Możesz też zresetować inne stany, jeśli to potrzebne, np. wyłączyć przycisk confirmGridButton
            // confirmGridButton.disabled = true; // Jeśli chcesz
            isGridConfirmed = false; // Na pewno resetujemy stan potwierdzenia siatki
            resetToStep1VisualsOnly(); // Przywróć wizualnie krok 1, jeśli byłeś dalej
            return; // Zakończ funkcję wcześniej
        }

        const mapId = selectedOption.value;
        const imageUrl = selectedOption.dataset.imageUrl;
        console.log(`Selected Map ID: ${mapId}, Image URL: ${imageUrl}`);


        if (!imageUrl) { // Dodatkowe zabezpieczenie, choć nie powinno się zdarzyć dla prawidłowych opcji
            console.error("Image URL is missing for the selected map!");
            mapBgImg.style.display = 'none';
            mapBgImg.src = '#';
            currentMapData = null;
            clearCanvasAndHide();
            return;
        }

        mapBgImg.style.display = 'block';
        mapBgImg.src = imageUrl;

        const newImg = mapBgImg.cloneNode(true);
        if (mapBgImg.parentNode) { // Sprawdź, czy rodzic istnieje przed próbą replaceChild
            mapBgImg.parentNode.replaceChild(newImg, mapBgImg);
        }
        mapBgImg = newImg;

        mapBgImg.onload = () => {
            // ... (reszta logiki onload bez zmian)
            console.log(`Map image loaded: ${mapBgImg.naturalWidth}x${mapBgImg.naturalHeight}`);
            currentMapData = {
                id: mapId,
                imageUrl: imageUrl,
                naturalWidth: mapBgImg.naturalWidth,
                naturalHeight: mapBgImg.naturalHeight
            };
            canvas.style.display = 'block';
            updateGridPreview();
            // confirmGridButton.disabled = false; // Włącz przycisk potwierdzenia, jeśli był wyłączony
        };

        mapBgImg.onerror = () => {
            resetToStep1VisualsOnly()
        };
    }

    // Dodaj funkcję pomocniczą do resetowania tylko wizualizacji kroku 1
    function resetToStep1VisualsOnly() {
        // Ta funkcja jest podobna do resetToStep1, ale nie zmienia logiki `isGridConfirmed`
        // ani nie odblokowuje pól, jeśli były zablokowane z innego powodu.
        // Używamy jej, gdy użytkownik odznacza mapę.

        // Pokaż krok 1, ukryj krok 2 (jeśli był widoczny)
        confirmGridButton.classList.remove('hidden-section');
        if (step1MapGridSelection) { // Sprawdź, czy elementy istnieją
            const formGroup = step1MapGridSelection.querySelector('.form-group');
            const formRow = step1MapGridSelection.querySelector('.form-row');
            if (formGroup) formGroup.style.opacity = 1;
            if (formRow) formRow.style.opacity = 1;
        }


        if (step2WaystonePlacement) step2WaystonePlacement.classList.add('hidden-section');
        if (canvas) canvas.style.pointerEvents = 'none';
        
        selectedColor = null;
        const currentSelectedColorButton = colorPaletteContainer ? colorPaletteContainer.querySelector('.selected') : null;
        if (currentSelectedColorButton) {
            currentSelectedColorButton.classList.remove('selected');
        }
        
        // updateGridPreview(); // Niekoniecznie chcemy rysować siatkę, jeśli nie ma mapy
        if (validationMessageEl) validationMessageEl.style.display = 'none';
        if (saveBoardButton) saveBoardButton.disabled = true;
    }

    function handleGridDimensionChange() {
        if (isGridConfirmed) return; // Nie aktualizuj siatki dynamicznie po zatwierdzeniu
        console.log("Grid dimensions changed.");
        updateGridPreview();
    }

function updateGridPreview() {
    // Sprawdź, czy obraz jest widoczny i ma wymiary
    if (!currentMapData || mapBgImg.style.display === 'none' || mapBgImg.clientWidth === 0 || mapBgImg.clientHeight === 0) {
        console.log("Cannot update grid preview: map not loaded/visible or image has no client dimensions.");
        clearCanvasAndHide();
        return;
    }

    const rows = parseInt(gridRowsInput.value);
    const cols = parseInt(gridColsInput.value);

    if (isNaN(rows) || isNaN(cols) || rows < 1 || cols < 1 || rows > 50 || cols > 50) {
        console.log("Invalid grid dimensions for preview.");
        if (canvas.style.display !== 'none') { // Tylko jeśli canvas był widoczny
             clearCanvas(); // Wyczyść, ale nie ukrywaj, jeśli mapa jest widoczna
        }
        return;
    }

    canvas.style.display = 'block';
    
    // Ustaw wymiary canvas DOKŁADNIE na wymiary wyświetlanego obrazka
    canvas.width = mapBgImg.clientWidth;
    canvas.height = mapBgImg.clientHeight;

    // Sprawdź, czy canvas otrzymał wymiary
    if (canvas.width === 0 || canvas.height === 0) {
        console.error("Canvas dimensions are zero after setting from mapBgImg.clientWidth/Height. Image might not be rendered yet or CSS issue.");
        // Można spróbować lekkiego opóźnienia, jeśli to problem z timingiem renderowania
        // setTimeout(updateGridPreview, 50); // Ostrożnie z tym, może prowadzić do pętli
        return;
    }


    grid.rows = rows;
    grid.cols = cols;
    grid.cellWidth = canvas.width / grid.cols;
    grid.cellHeight = canvas.height / grid.rows;

    console.log(`Grid Preview - Canvas: ${canvas.width}x${canvas.height}, Cell: ${grid.cellWidth}x${grid.cellHeight}`);
    drawGridOnly();
}

function drawGridOnly() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!grid || grid.rows === 0 || grid.cols === 0 || canvas.width === 0 || canvas.height === 0 || !grid.cellWidth || !grid.cellHeight) {
        // console.warn("drawGridOnly: Aborting due to invalid parameters.");
        return;
    }

    const cWidth = canvas.width;
    const cHeight = canvas.height;

    // --- 1. Draw INNER grid lines ---
    ctx.strokeStyle = 'rgba(255, 170, 0, 0.9)'; // Your orange for inner lines
    ctx.lineWidth = 1;                         // Inner lines width

    // Vertical inner lines: loop from 1 up to (but not including) grid.cols
    for (let i = 1; i < grid.cols; i++) {
        // Draw at x.5 for sharper 1px lines
        const x = Math.floor(i * grid.cellWidth) + 0.5;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, cHeight);
        ctx.stroke();
    }
    // Horizontal inner lines: loop from 1 up to (but not including) grid.rows
    for (let i = 1; i < grid.rows; i++) {
        // Draw at y.5 for sharper 1px lines
        const y = Math.floor(i * grid.cellHeight) + 0.5;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(cWidth, y);
        ctx.stroke();
    }

    // --- 2. Draw the BORDER around the entire grid ---
    const BORDER_COLOR = 'rgba(255, 170, 0, 0.9)'; // Example: Darker border color
    const BORDER_WIDTH = 2;                    // Example: Thicker border width

    ctx.strokeStyle = BORDER_COLOR;
    ctx.lineWidth = BORDER_WIDTH;

    // For a 2px border, drawing centered at 1px from the edge covers pixels 0 and 1
    // and pixels (dim-2) and (dim-1) at the far edge.

    // Top border line (covers pixel rows 0 and 1)
    ctx.beginPath();
    ctx.moveTo(0, 1); // Line centered at y=1
    ctx.lineTo(cWidth, 1);
    ctx.stroke();

    // Bottom border line (covers pixel rows cHeight-2 and cHeight-1)
    ctx.beginPath();
    ctx.moveTo(0, cHeight - 1); // Line centered at y=cHeight-1
    ctx.lineTo(cWidth, cHeight - 1);
    ctx.stroke();

    // Left border line (covers pixel columns 0 and 1)
    ctx.beginPath();
    ctx.moveTo(1, 0); // Line centered at x=1
    ctx.lineTo(1, cHeight);
    ctx.stroke();

    // Right border line (covers pixel columns cWidth-2 and cWidth-1)
    ctx.beginPath();
    ctx.moveTo(cWidth - 1, 0); // Line centered at x=cWidth-1
    ctx.lineTo(cWidth - 1, cHeight);
    ctx.stroke();
}
    
    function clearCanvas() {
        if (canvas && ctx) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }

    function clearCanvasAndHide() {
        clearCanvas();
        if (canvas) canvas.style.display = 'none';
    }


    function confirmGridAndProceedToStep2() {
        if (!currentMapData) {
            alert("Najpierw wybierz mapę.");
            return;
        }
        const rows = parseInt(gridRowsInput.value);
        const cols = parseInt(gridColsInput.value);
        if (isNaN(rows) || isNaN(cols) || rows < 1 || cols < 1 || rows > 50 || cols > 50) {
            alert("Podaj poprawne wymiary siatki (1-50) przed zatwierdzeniem.");
            return;
        }

        isGridConfirmed = true;
        // Zablokuj edycję mapy i siatki
        mapSelect.disabled = true;
        gridRowsInput.disabled = true;
        gridColsInput.disabled = true;
        
        // Pokaż krok 2, ukryj krok 1 (tylko przycisk)
        confirmGridButton.classList.add('hidden-section'); // Ukryj przycisk zatwierdzania siatki
        step1MapGridSelection.querySelector('.form-group').style.opacity = 0.5; // Przyciemnij wybór mapy
        step1MapGridSelection.querySelector('.form-row').style.opacity = 0.5;   // Przyciemnij wybór wymiarów

        step2WaystonePlacement.classList.remove('hidden-section');
        canvas.style.pointerEvents = 'auto'; // Włącz klikanie na canvas

        // Zresetuj kamienie i narysuj siatkę + istniejące kamienie (jeśli jakieś były z poprzedniego resetu)
        waystones = []; // Zawsze zaczynaj z czystą planszą kamieni po zatwierdzeniu nowej siatki
        drawGridAndWaystonesFull();
        validateBoard(); // Sprawdź walidację (powinna być niepoprawna na początku)
        console.log("Grid confirmed. Proceeding to waystone placement.");
    }


    // --- KROK 2: Logika Kamieni Drogi ---
    function handleColorSelection(event) {
        const targetButton = event.target.closest('button');
        if (!targetButton) return;

        const currentSelected = colorPaletteContainer.querySelector('.selected');
        if (currentSelected) {
            currentSelected.classList.remove('selected');
        }
        selectedColor = targetButton.dataset.color;
        targetButton.classList.add('selected');
        console.log("Selected color:", selectedColor);
    }

    function handleCanvasClick(event) {
        if (!isGridConfirmed || !selectedColor) {
            if (!selectedColor) alert("Wybierz kolor lub gumkę z palety.");
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        const col = Math.floor(x / grid.cellWidth);
        const row = Math.floor(y / grid.cellHeight);

        if (col < 0 || col >= grid.cols || row < 0 || row >= grid.rows) return;

        const existingWaystoneIndex = waystones.findIndex(ws => ws.row === row && ws.col === col);

        if (selectedColor === 'eraser') {
            if (existingWaystoneIndex !== -1) {
                waystones.splice(existingWaystoneIndex, 1);
            }
        } else {
            if (existingWaystoneIndex !== -1) {
                const existingWs = waystones[existingWaystoneIndex];
                if (existingWs.color === selectedColor) {
                    waystones.splice(existingWaystoneIndex, 1);
                } else {
                    existingWs.color = selectedColor;
                }
            } else {
                waystones.push({ row, col, color: selectedColor });
            }
        }
        drawGridAndWaystonesFull();
        validateBoard();
    }

    function drawGridAndWaystonesFull() {
        drawGridOnly(); // Najpierw rysuj siatkę
        if (waystones.length === 0) return; // Jeśli nie ma kamieni, nie rób nic więcej

        // Rysuj Kamienie Drogi
        waystones.forEach(ws => {
            const centerX = (ws.col + 0.5) * grid.cellWidth;
            const centerY = (ws.row + 0.5) * grid.cellHeight;
            const radius = Math.min(grid.cellWidth, grid.cellHeight) * 0.4;

            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI, false);
            ctx.fillStyle = ws.color;
            ctx.fill();
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 1;
            ctx.stroke();
        });
    }

    function resetToStep1() {
        isGridConfirmed = false;
        // Odblokuj edycję mapy i siatki
        mapSelect.disabled = false;
        gridRowsInput.disabled = false;
        gridColsInput.disabled = false;

        // Pokaż krok 1, ukryj krok 2
        confirmGridButton.classList.remove('hidden-section');
        step1MapGridSelection.querySelector('.form-group').style.opacity = 1;
        step1MapGridSelection.querySelector('.form-row').style.opacity = 1;

        step2WaystonePlacement.classList.add('hidden-section');
        canvas.style.pointerEvents = 'none'; // Wyłącz klikanie na canvas
        
        // Nie czyść waystones, jeśli użytkownik chce tylko zmienić siatkę i wrócić
        // waystones = []; 
        selectedColor = null; // Zresetuj wybrany kolor
        const currentSelectedColorButton = colorPaletteContainer.querySelector('.selected');
        if (currentSelectedColorButton) {
            currentSelectedColorButton.classList.remove('selected');
        }
        
        updateGridPreview(); // Prerysuj samą siatkę
        validationMessageEl.style.display = 'none';
        saveBoardButton.disabled = true;
        console.log("Reset to step 1 (map/grid selection).");
    }


    // --- Walidacja i Zapis ---
    function validateBoard() {
        // Ta funkcja pozostaje w dużej mierze taka sama
        let isValid = true;
        let messages = [];
        const colorCounts = {};

        WAYSTONE_COLORS_DATA.forEach(colorTuple => {
            colorCounts[colorTuple[0]] = 0;
        });
        waystones.forEach(ws => {
            if (colorCounts.hasOwnProperty(ws.color)) {
                colorCounts[ws.color]++;
            }
        });
        WAYSTONE_COLORS_DATA.forEach(colorTuple => {
            const colorCode = colorTuple[0];
            const colorName = colorTuple[1]; // Nazwa koloru dla komunikatu
            const count = colorCounts[colorCode];
            if (count !== 0 && count !== 2) {
                isValid = false;
                messages.push(`Kolor ${colorName} (${colorCode}) ma ${count} kamieni (oczekiwano 0 lub 2).`);
            }
        });

        if (!boardNameInput.value.trim()) {
             isValid = false;
             messages.unshift("Nazwa planszy jest wymagana.");
        }
        if (!isGridConfirmed) { // Dodatkowe sprawdzenie, czy siatka jest zatwierdzona
            isValid = false;
            // Nie dodawaj komunikatu, bo przycisk zapisu i tak jest ukryty
        }


        if (isValid && isGridConfirmed) {
            validationMessageEl.textContent = 'Plansza jest POPRAWNA.';
            validationMessageEl.className = 'alert alert-success';
            saveBoardButton.disabled = false;
        } else {
            if (isGridConfirmed) { // Pokazuj błędy tylko jeśli jesteśmy w kroku 2
                validationMessageEl.innerHTML = 'Plansza jest NIEPOPRAWNA:<br>' + messages.join('<br>');
                validationMessageEl.className = 'alert alert-danger';
            } else {
                validationMessageEl.style.display = 'none'; // Ukryj, jeśli nie jesteśmy na etapie kamieni
            }
            saveBoardButton.disabled = true;
        }
        if (isGridConfirmed) { // Pokazuj/ukrywaj komunikat walidacji
             validationMessageEl.style.display = messages.length > 0 || isValid ? 'block' : 'none';
        }
        return isValid;
    }

    async function saveBoard() {
        if (!isGridConfirmed || !validateBoard()) { // Sprawdź też isGridConfirmed
            alert("Nie można zapisać niepoprawnej lub niezatwierdzonej planszy.");
            return;
        }
        // Dane do zapisu pobieramy z aktualnego stanu
        const boardData = {
            name: boardNameInput.value.trim(),
            map_reference: parseInt(currentMapData.id),
            grid_rows: parseInt(gridRowsInput.value), // Pobierz aktualne wartości, bo mogły być zmienione przed resetem
            grid_cols: parseInt(gridColsInput.value),
            waystones_input: waystones
        };

        saveBoardButton.disabled = true;
        saveBoardButton.textContent = 'Zapisywanie...';

        try {
            const response = await fetch(API_BOARDS_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify(boardData)
            });

            if (response.ok) {
                const responseData = await response.json();
                alert(`Plansza "${responseData.name}" zapisana pomyślnie!`);
                window.location.href = "/"; // Użyj Django URL tag w JS, jeśli jest w bloku <script> szablonu
                                                      // Lub twardo zakoduj, np. '/'
            } else {
                const errorData = await response.json();
                let errorMessages = "Błąd zapisu planszy:\n";
                for (const key in errorData) {
                    errorMessages += `${key}: ${Array.isArray(errorData[key]) ? errorData[key].join(', ') : errorData[key]}\n`;
                }
                alert(errorMessages);
            }
        } catch (error) {
            console.error('Błąd sieci lub serwera:', error);
            alert('Wystąpił nieoczekiwany błąd. Spróbuj ponownie.');
        } finally {
            // Niezależnie od wyniku, przywróć przycisk, chyba że przekierowano
            if (!response || !response.ok) { // Tylko jeśli nie było sukcesu i przekierowania
                 saveBoardButton.disabled = false;
                 saveBoardButton.textContent = 'Zapisz Planszę';
            }
        }
    }
    
    // Uruchomienie inicjalizacji UI po załadowaniu DOM
    initializeUI();

    // Dodatkowe: Nasłuchiwanie na resize, aby przerysować siatkę (opcjonalne, może wymagać dopracowania)
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (currentMapData && mapBgImg.clientWidth > 0) { // Tylko jeśli mapa jest załadowana
                console.log("Window resized, updating grid preview/full draw.");
                if (isGridConfirmed) {
                    // Trzeba zaktualizować wymiary canvas i komórek, a potem przerysować wszystko
                    canvas.width = mapBgImg.clientWidth;
                    canvas.height = mapBgImg.clientHeight;
                    grid.cellWidth = canvas.width / grid.cols;
                    grid.cellHeight = canvas.height / grid.rows;
                    drawGridAndWaystonesFull();
                } else {
                    updateGridPreview();
                }
            }
        }, 250); // Debounce
    });

});