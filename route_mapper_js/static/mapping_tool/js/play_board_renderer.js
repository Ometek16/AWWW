// static/mapping_tool/js/play_board_renderer.js
document.addEventListener('DOMContentLoaded', () => {
    const boardDataContainer = document.getElementById('board-data-for-js-container');
    const mapDisplayImg = document.getElementById('map-display-img');
    const playGridCanvas = document.getElementById('play-grid-canvas');
    const ctx = playGridCanvas.getContext('2d');
    const loadingPlaceholder = document.getElementById('loading-placeholder');
    const toolPalette = document.querySelector('.tool-palette'); // Kontener na narzędzia

    if (!boardDataContainer || !mapDisplayImg || !playGridCanvas || !loadingPlaceholder || !toolPalette) {
        console.error("Brakuje kluczowych elementów DOM.");
        if(loadingPlaceholder) loadingPlaceholder.textContent = "Błąd inicjalizacji UI.";
        return;
    }

    let boardData;
    let grid = { rows: 0, cols: 0, cellWidth: 0, cellHeight: 0 }; // Przechowuj info o siatce
    let userPaths = []; // Ścieżki rysowane przez użytkownika w tej sesji
    let currentTool = 'none'; // 'pencil', 'eraser', 'none'
    let isDrawing = false;
    let currentPathStartCell = null;
    let currentPathPreview = null;

    // Konfiguracja rysowania ścieżek
    const PATH_COLOR = 'rgba(0, 123, 255, 0.9)'; // Niebieski, Bootstrap primary
    const PATH_LINE_WIDTH = 4; // Gruba linia
    const PATH_PREVIEW_COLOR = 'rgba(0, 123, 255, 0.4)';
    const ERASER_RADIUS = 10; // Piksele - promień gumki do ścieżek

    try {
        boardData = JSON.parse(boardDataContainer.textContent);
        console.log("Play mode: Board data loaded:", boardData);
    } catch (e) {
        console.error("Play mode: Błąd parsowania JSON:", e);
        loadingPlaceholder.textContent = "Błąd ładowania danych planszy.";
        return;
    }

    if (!boardData || !boardData.map_details || !boardData.map_details.image) {
        console.error("Play mode: Niekompletne dane planszy.");
        loadingPlaceholder.textContent = "Niekompletne dane planszy.";
        return;
    }

    const boardId = boardData.id; // Pobierz ID aktualnej planszy
    const userPathsApiEndpoint = `/api/boards/${boardId}/user-paths/`;

    // --- Inicjalizacja Narzędzi ---
    toolPalette.addEventListener('click', (event) => {
        const button = event.target.closest('button[data-tool]');
        if (!button) return;

        toolPalette.querySelectorAll('button').forEach(btn => btn.classList.remove('selected'));
        button.classList.add('selected');
        currentTool = button.dataset.tool;
        console.log("Selected tool:", currentTool);

        // Zmień kursor canvasa w zależności od narzędzia
        if (currentTool === 'pencil') {
            playGridCanvas.style.cursor = 'crosshair';
        } else if (currentTool === 'eraser') {
            playGridCanvas.style.cursor = `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'><circle cx='12' cy='12' r='${ERASER_RADIUS -1}' fill='none' stroke='black' stroke-width='1'/><circle cx='12' cy='12' r='${ERASER_RADIUS}' fill='rgba(255,0,0,0.3)'/></svg>") ${ERASER_RADIUS} ${ERASER_RADIUS}, auto`;
        } else {
            playGridCanvas.style.cursor = 'default';
        }

        // Anuluj rysowanie, jeśli zmieniono narzędzie w trakcie
        isDrawing = false;
        currentPathStartCell = null;
        currentPathPreview = null;
        drawBoardState(); // Prerysuj, aby usunąć podgląd
    });


    // --- Ładowanie Mapy i Ustawianie Canvasa ---
    mapDisplayImg.src = boardData.map_details.image;
    mapDisplayImg.style.display = 'block';

    mapDisplayImg.onload = () => {
        if(loadingPlaceholder) loadingPlaceholder.style.display = 'none';
        console.log(`Play mode: Map image loaded ${mapDisplayImg.clientWidth}x${mapDisplayImg.clientHeight}`);
        
        playGridCanvas.width = mapDisplayImg.clientWidth;
        playGridCanvas.height = mapDisplayImg.clientHeight;
        playGridCanvas.style.display = 'block'; // Pokaż canvas

        if (playGridCanvas.width > 0 && playGridCanvas.height > 0) {
            grid.rows = boardData.grid_rows;
            grid.cols = boardData.grid_cols;
            grid.cellWidth = playGridCanvas.width / grid.cols;
            grid.cellHeight = playGridCanvas.height / grid.rows;
            loadUserPaths();
        } else { /* ... obsługa błędu ... */ }
    };
    mapDisplayImg.onerror = () => { /* ... obsługa błędu ... */ };


    // --- Funkcje Rysujące ---
    function drawBoardState() {
        ctx.clearRect(0, 0, playGridCanvas.width, playGridCanvas.height);
        if (grid.rows === 0 || grid.cols === 0) return;

        // 1. Rysuj siatkę (subtelnie)
        ctx.strokeStyle = 'rgba(180, 180, 180, 0.25)';
        ctx.lineWidth = 1;
        for (let i = 1; i < grid.cols; i++) {
            const x = Math.floor(i * grid.cellWidth) + 0.5;
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, playGridCanvas.height); ctx.stroke();
        }
        for (let i = 1; i < grid.rows; i++) {
            const y = Math.floor(i * grid.cellHeight) + 0.5;
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(playGridCanvas.width, y); ctx.stroke();
        }
        // (Opcjonalnie) Ramka planszy
        // ctx.strokeStyle = 'rgba(100, 100, 100, 0.4)';
        // ctx.strokeRect(0.5, 0.5, playGridCanvas.width - 1, playGridCanvas.height - 1);

        // 2. Rysuj zapisane przez użytkownika ścieżki
        userPaths.forEach(path => {
            drawPathSegment(path.start, path.end, PATH_COLOR, PATH_LINE_WIDTH);
        });

        // 3. Rysuj podgląd aktualnie rysowanej ścieżki
        if (isDrawing && currentTool === 'pencil' && currentPathPreview) {
            drawPathSegment(currentPathPreview.start, currentPathPreview.end, PATH_PREVIEW_COLOR, PATH_LINE_WIDTH, true);
        }

        // 4. Rysuj predefiniowane Waystone'y
        if (boardData.waystones && boardData.waystones.length > 0) {
            boardData.waystones.forEach(ws => {
                const centerX = (ws.col + 0.5) * grid.cellWidth;
                const centerY = (ws.row + 0.5) * grid.cellHeight;
                const radius = Math.min(grid.cellWidth, grid.cellHeight) * 0.35; // Nieco mniejsze
                ctx.beginPath();
                ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
                ctx.fillStyle = ws.color;
                ctx.fill();
                ctx.strokeStyle = '#555'; ctx.lineWidth = 1; ctx.stroke();
            });
        }
    }

    function drawPathSegment(startCell, endCell, color, lineWidth, isDashed = false) {
        if (!startCell || !endCell || grid.cellWidth === 0 || grid.cellHeight === 0) return;
        const startX = (startCell.col + 0.5) * grid.cellWidth;
        const startY = (startCell.row + 0.5) * grid.cellHeight;
        const endX = (endCell.col + 0.5) * grid.cellWidth;
        const endY = (endCell.row + 0.5) * grid.cellHeight;

        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.lineCap = 'round'; // Zaokrąglone końce linii
        ctx.lineJoin = 'round'; // Zaokrąglone łączenia
        if (isDashed) ctx.setLineDash([8, 8]);
        ctx.stroke();
        if (isDashed) ctx.setLineDash([]);
    }

    function getCellFromMouseEvent(event) {
        // ... (bez zmian, ale upewnij się, że grid.cellWidth/Height są > 0) ...
        if (!grid || grid.cellWidth === 0 || grid.cellHeight === 0) return null;
        const rect = playGridCanvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const col = Math.floor(x / grid.cellWidth);
        const row = Math.floor(y / grid.cellHeight);
        if (col < 0 || col >= grid.cols || row < 0 || row >= grid.rows) return null;
        return { row, col };
    }


    // --- Obsługa Myszki dla Rysowania/Gumki ---
    playGridCanvas.addEventListener('mousedown', (event) => {
        if (event.button !== 0 || grid.rows === 0) return; // Tylko lewy przycisk, tylko gdy siatka jest załadowana
        const cell = getCellFromMouseEvent(event);
        if (!cell) return;

        if (currentTool === 'pencil') {
            isDrawing = true;
            currentPathStartCell = cell;
            console.log("Pencil: Start drawing at", cell);
        } else if (currentTool === 'eraser') {
            erasePathsNearPoint(event.clientX - playGridCanvas.getBoundingClientRect().left, event.clientY - playGridCanvas.getBoundingClientRect().top);
            drawBoardState(); // Prerysuj po potencjalnym usunięciu
        }
    });

    playGridCanvas.addEventListener('mousemove', (event) => {
        if (currentTool === 'pencil' && isDrawing && currentPathStartCell) {
            const currentCell = getCellFromMouseEvent(event);
            if (currentCell) {
                if (!currentPathPreview || currentPathPreview.end.row !== currentCell.row || currentPathPreview.end.col !== currentCell.col) {
                    if (currentPathStartCell.row !== currentCell.row || currentPathStartCell.col !== currentCell.col) {
                        currentPathPreview = { start: currentPathStartCell, end: currentCell };
                    } else {
                        currentPathPreview = null;
                    }
                    drawBoardState();
                }
            } else { // Mysz poza siatką
                if (currentPathPreview) { // Jeśli był podgląd, usuń go
                    currentPathPreview = null;
                    drawBoardState();
                }
            }
        } else if (currentTool === 'eraser' && event.buttons === 1) { // Gumka działa też przy przeciąganiu
             erasePathsNearPoint(event.clientX - playGridCanvas.getBoundingClientRect().left, event.clientY - playGridCanvas.getBoundingClientRect().top);
             drawBoardState();
        }
    });

    playGridCanvas.addEventListener('mouseup', (event) => {
        if (event.button !== 0) return;
        if (currentTool === 'pencil' && isDrawing && currentPathStartCell) {
            const endCell = getCellFromMouseEvent(event);
            currentPathPreview = null; // Zawsze usuwaj podgląd po mouseup
            if (endCell && (endCell.row !== currentPathStartCell.row || endCell.col !== currentPathStartCell.col)) {
                userPaths.push({ start: currentPathStartCell, end: endCell }); // Kolor i grubość zdefiniowane w PATH_COLOR, PATH_LINE_WIDTH
                console.log("Pencil: Path segment added", userPaths[userPaths.length - 1]);
                saveUserPaths(); 
            } else {
                console.log("Pencil: Drawing ended in same cell or outside, no segment.");
            }
        }
        isDrawing = false;
        currentPathStartCell = null;
        drawBoardState(); // Finalne przerysowanie
    });

    playGridCanvas.addEventListener('mouseleave', () => {
        if (currentTool === 'pencil' && isDrawing) {
            console.log("Pencil: Mouse left canvas during drawing, preview cleared.");
            currentPathPreview = null;
            // Nie kończymy tu rysowania, użytkownik może wrócić. Mouseup to zrobi.
            drawBoardState();
        }
    });

    function erasePathsNearPoint(mouseX, mouseY) {
        let pathErasedThisTime = false;
        // Iteruj od końca, aby bezpiecznie usuwać elementy
        for (let i = userPaths.length - 1; i >= 0; i--) {
            const path = userPaths[i];
            // Sprawdź, czy path i path.start/end istnieją, na wszelki wypadek
            if (!path || !path.start || !path.end) {
                console.warn("erasePathsNearPoint: Encountered invalid path segment, skipping.", path);
                continue;
            }
            // Sprawdź, czy grid.cellWidth i grid.cellHeight są zdefiniowane i nie są zerowe
            if (!grid || grid.cellWidth === 0 || grid.cellHeight === 0) {
                console.warn("erasePathsNearPoint: Grid cell dimensions are invalid, cannot calculate path coordinates.");
                return false; // Nie można kontynuować bez wymiarów komórek
            }

            const startX = (path.start.col + 0.5) * grid.cellWidth;
            const startY = (path.start.row + 0.5) * grid.cellHeight;
            const endX = (path.end.col + 0.5) * grid.cellWidth;
            const endY = (path.end.row + 0.5) * grid.cellHeight;

            // Definicja distToLine MUSI być tutaj, wewnątrz pętli, przed jej użyciem
            const distToLine = distanceToLineSegment(mouseX, mouseY, startX, startY, endX, endY);

            if (distToLine < ERASER_RADIUS + PATH_LINE_WIDTH / 2) { // Jeśli gumka dotyka linii
                userPaths.splice(i, 1);
                pathErasedThisTime = true;
                // Nie loguj tutaj, zrobimy to raz po pętli, jeśli cokolwiek usunięto
            }
        }

        if (pathErasedThisTime) {
            console.log("Eraser: Path segment(s) removed from JS array.");
            saveUserPaths(); // Zapisz zmiany na serwerze
        }
        return pathErasedThisTime;
    }

    // Funkcja pomocnicza do obliczania odległości punktu (px, py) od segmentu linii (x1,y1)-(x2,y2)
    function distanceToLineSegment(px, py, x1, y1, x2, y2) {
        const l2 = (x1 - x2)**2 + (y1 - y2)**2;
        if (l2 === 0) return Math.sqrt((px - x1)**2 + (py - y1)**2);
        let t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2;
        t = Math.max(0, Math.min(1, t));
        const nearestX = x1 + t * (x2 - x1);
        const nearestY = y1 + t * (y2 - y1);
        return Math.sqrt((px - nearestX)**2 + (py - nearestY)**2);
    }

    // --- Resize Listener --- (bez zmian, ale upewnij się, że poprawnie przelicza grid i wywołuje drawBoardState)
    let resizeTimerPlay;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimerPlay);
        resizeTimerPlay = setTimeout(() => {
            if (mapDisplayImg.style.display !== 'none' && mapDisplayImg.clientWidth > 0) {
                console.log("Play mode: Window resized, redrawing board.");
                playGridCanvas.width = mapDisplayImg.clientWidth;
                playGridCanvas.height = mapDisplayImg.clientHeight;
                if (playGridCanvas.width > 0 && playGridCanvas.height > 0 && boardData) { // Sprawdź boardData
                    grid.rows = boardData.grid_rows; // Upewnij się, że grid jest aktualny
                    grid.cols = boardData.grid_cols;
                    grid.cellWidth = playGridCanvas.width / grid.cols;
                    grid.cellHeight = playGridCanvas.height / grid.rows;
                    drawBoardState();
                }
            }
        }, 250);
    });


    async function loadUserPaths() {
        console.log("Play mode: Loading user paths from", userPathsApiEndpoint);
        try {
            const response = await fetch(userPathsApiEndpoint, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN // Jeśli API wymaga CSRF dla GET z sesją
                }
            });
            if (response.ok) {
                const loadedPathSegments = await response.json();
                userPaths = loadedPathSegments.map(segment => ({ // Dopasuj do formatu używanego w JS
                    start: { row: segment.start_row, col: segment.start_col },
                    end: { row: segment.end_row, col: segment.end_col },
                    // color: segment.color || PATH_COLOR // Jeśli zapisujesz kolor
                }));
                console.log("Play mode: User paths loaded:", userPaths);
            } else {
                console.error("Play mode: Failed to load user paths", response.status, await response.text());
                userPaths = []; // W razie błędu zacznij z pustymi
            }
        } catch (error) {
            console.error("Play mode: Network error loading user paths:", error);
            userPaths = [];
        }
        drawBoardState(); // Zawsze przerysuj po próbie wczytania
    }

    async function saveUserPaths() {
        if (!boardId) return; // Nie rób nic, jeśli nie ma ID planszy
        console.log("Play mode: Saving user paths to", userPathsApiEndpoint, userPaths);

        // Przygotuj dane do wysłania (backend oczekuje start_row, start_col etc.)
        const payload = userPaths.map(p => ({
            start_row: p.start.row,
            start_col: p.start.col,
            end_row: p.end.row,
            end_col: p.end.col,
            // color: p.color // Jeśli wysyłasz kolor
        }));

        try {
            const response = await fetch(userPathsApiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify(payload)
            });
            if (response.ok) {
                const savedPathsData = await response.json();
                console.log("Play mode: User paths saved successfully.", savedPathsData);
                // Opcjonalnie zaktualizuj userPaths o ID z serwera, jeśli to potrzebne
                // userPaths = savedPathsData.map(segment => ({...}));
            } else {
                console.error("Play mode: Failed to save user paths", response.status, await response.text());
                alert("Błąd podczas zapisywania ścieżek na serwerze.");
            }
        } catch (error) {
            console.error("Play mode: Network error saving user paths:", error);
            alert("Błąd sieci podczas zapisywania ścieżek.");
        }
    }

    // Modyfikacja playGridCanvas.addEventListener('mouseup', ...)
    playGridCanvas.addEventListener('mouseup', (event) => {
        if (event.button !== 0) return;
        if (currentTool === 'pencil' && isDrawing && currentPathStartCell) {
            const endCell = getCellFromMouseEvent(event);
            currentPathPreview = null;
            if (endCell && (endCell.row !== currentPathStartCell.row || endCell.col !== currentPathStartCell.col)) {
                userPaths.push({ 
                    start: currentPathStartCell, 
                    end: endCell,
                    // color: PATH_COLOR // Możesz dodać, jeśli przechowujesz w userPaths
                });
                console.log("Pencil: Path segment added", userPaths[userPaths.length - 1]);
                saveUserPaths(); // ZAPISZ ŚCIEŻKI PO DODANIU NOWEGO SEGMENTU
            } else { /* ... */ }
        }
        isDrawing = false;
        currentPathStartCell = null;
        drawBoardState();
    });
});