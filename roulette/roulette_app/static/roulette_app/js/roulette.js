console.log("roulette.js loaded and executing!");

document.addEventListener('DOMContentLoaded', () => {
    const rouletteGame = document.getElementById('roulette-game');

    if (rouletteGame) {
        console.log("User is logged in, roulette game area is present. Initializing game logic...");

        const spinButton = document.getElementById('spin-button');
        const rouletteWheel = document.getElementById('roulette-wheel');
        const resultDisplay = document.getElementById('result-display');
        const recentOnesTableBody = document.querySelector('#recent-ones-table tbody');
        const notificationContainer = document.getElementById('notification-container');
        const leftNotificationContainer = document.getElementById('left-notification-container');

        let isWheelAnimating = false; // Flag for *local* wheel animation

        // Retrieve current user data embedded in index.html (from Step 1)
        const currentUserId = typeof window.currentUserId !== 'undefined' ? window.currentUserId : null;
        const currentUsername = typeof window.currentUsername !== 'undefined' ? window.currentUsername : 'Guest';

        // Helper function to get CSRF token from cookies
        function getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        const csrftoken = getCookie('csrftoken');

        // --- Reusable Animation Function (from Step 6) ---
        function animateWheel(rolledNumber, initiatorUsername) {
            if (isWheelAnimating) {
                console.log("Wheel is already animating, skipping new animation.");
                return;
            }
            isWheelAnimating = true;
            spinButton.disabled = true; // Disable button while animating

            const baseRotation = 360 * 5; // Spin 5 full rotations

            let targetAngle = 0;
            switch (rolledNumber) {
                case 1: targetAngle = 20 + 0; break;
                case 2: targetAngle = 20 + 72; break;
                case 3: targetAngle = 20 + 144; break;
                case 4: targetAngle = 20 + 216; break;
                case 5: targetAngle = 20 + 288; break;
            }

            const finalRotation = baseRotation + targetAngle;

            rouletteWheel.style.transition = 'none';
            rouletteWheel.style.transform = `rotate(0deg)`;
            rouletteWheel.offsetHeight; // Force reflow

            rouletteWheel.style.transition = 'transform 4s cubic-bezier(0.25, 0.1, 0.25, 1)';
            rouletteWheel.style.transform = `rotate(-${finalRotation}deg)`;

            rouletteWheel.addEventListener('transitionend', function handler(event) {
                if (event.propertyName === 'transform') {
                    resultDisplay.textContent = `${initiatorUsername} rolled a ${rolledNumber}!`;
                    spinButton.disabled = false; // Re-enable button
                    isWheelAnimating = false;
                    rouletteWheel.removeEventListener('transitionend', handler);
                }
            }, { once: true });
        }

        // --- Frontend-Backend Spin Integration & Result Display (from Step 7) ---
        spinButton.addEventListener('click', () => {
            if (isWheelAnimating) {
                console.log("Already spinning, please wait.");
                return;
            }

            resultDisplay.textContent = "Requesting spin...";

            fetch('/spin/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json'
                },
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 403) {
                        alert("You must be logged in to spin the wheel.");
                        window.location.href = '/accounts/login/?next=' + window.location.pathname;
                    }
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    animateWheel(data.rolled_number, 'You');
                } else {
                    resultDisplay.textContent = "Spin failed.";
                    spinButton.disabled = false;
                    isWheelAnimating = false;
                    console.error("Spin request was successful but data indicated failure:", data.message);
                }
            })
            .catch(error => {
                console.error("Error during spin:", error);
                resultDisplay.textContent = "An error occurred.";
                spinButton.disabled = false;
                isWheelAnimating = false;
            });
        });

        // --- Step 10: Populate Recent "1" Rolls List Function (for Table) ---
        function populateRecentOnesList(rolls) {
            recentOnesTableBody.innerHTML = '';
            if (rolls.length === 0) {
                const tr = document.createElement('tr');
                const td = document.createElement('td');
                td.setAttribute('colspan', '2');
                td.textContent = 'No Option 1 rolls yet.';
                tr.appendChild(td);
                recentOnesTableBody.appendChild(tr);
                return;
            }
            rolls.forEach(roll => {
                const tr = document.createElement('tr');
                const userTd = document.createElement('td');
                const timeTd = document.createElement('td');

                userTd.textContent = roll.username;
                timeTd.textContent = new Date(roll.timestamp).toLocaleTimeString();

                tr.appendChild(userTd);
                tr.appendChild(timeTd);
                recentOnesTableBody.appendChild(tr);
            });
        }

        // Fetch initial recent ones on page load
        fetch('/api/recent-ones/')
            .then(response => response.json())
            .then(data => {
                populateRecentOnesList(data.recent_ones);
            })
            .catch(error => console.error('Error fetching recent ones:', error));

        // --- Step 11: Show Global Pop-up Notification (auto-dismissing) ---
        function showNotification(message) {
            const notificationDiv = document.createElement('div');
            notificationDiv.classList.add('notification');
            notificationDiv.textContent = message;
            notificationContainer.appendChild(notificationDiv);

            setTimeout(() => {
                notificationDiv.remove();
            }, 4500);
        }

        // --- Step 13: Show Global Pop-up Notification for Hand-Closed ('2's) ---
        function showHandCloseNotification(message) {
            const notificationDiv = document.createElement('div');
            notificationDiv.classList.add('hand-close-notification');
            notificationDiv.innerHTML = `
                <button class="close-btn">×</button>
                <p>${message}</p>
            `;

            notificationDiv.querySelector('.close-btn').addEventListener('click', () => {
                notificationDiv.remove();
            });

            leftNotificationContainer.appendChild(notificationDiv);
        }

        // --- ZMIANA DLA KROKU D: Zastąpienie SSE WebSocketem ---
        // Użyj 'ws://' lub 'wss://' w zależności od tego, czy używasz HTTPS
        // window.location.host automatycznie pobierze "127.0.0.1:8000"
        const websocket = new WebSocket('wss://' + window.location.host + '/ws/roulette/');

        websocket.onopen = () => {
            console.log('WebSocket connection opened.');
        };

        // ZMIANA DLA KROKU D: Teraz wszystkie wiadomości przychodzą przez onmessage
        websocket.onmessage = (event) => {
            console.log('WebSocket message received:', event.data);
            const data = JSON.parse(event.data);

            if (data.type === 'roulette_message') {
                const rollData = data.message;
                console.log('Parsed rollData:', rollData);

                if (rollData.user_id !== currentUserId) {
                    console.log(`Remote spin detected: ${rollData.username} rolled ${rollData.rolled_number}.`);
                } else {
                    console.log(`Own spin detected via WebSocket: ${rollData.username} rolled ${rollData.rolled_number}. Already handled locally.`);
                }

                // === KROK 1: SPRAWDŹ, CZY WARUNEK JEST SPEŁNIONY ===
                // ==================================================
                if (rollData.rolled_number === 1) {
                    console.log('Rolled a 1! Attempting to update scoreboard.');
                    // Poniżej też dodamy logi
                    const tr = document.createElement('tr');
                    const userTd = document.createElement('td');
                    const timeTd = document.createElement('td');

                    userTd.textContent = rollData.username;
                    timeTd.textContent = new Date(rollData.timestamp).toLocaleTimeString();

                    tr.appendChild(userTd);
                    tr.appendChild(timeTd);

                    recentOnesTableBody.prepend(tr);

                    if (recentOnesTableBody.children.length > 1 && recentOnesTableBody.lastChild.textContent === 'No Option 1 rolls yet.') {
                        recentOnesTableBody.lastChild.remove();
                    }

                    while (recentOnesTableBody.children.length > 10) {
                        recentOnesTableBody.removeChild(recentOnesTableBody.lastChild);
                    }
                  // === KROK 2: SPRAWDŹ, CZY TABLICA SIĘ AKTUALIZUJE ===
                  console.log("Zawartość tablicy po potencjalnej aktualizacji:");
                  for (let i = 0; i < recentOnesTableBody.children.length; i++) {
                      console.log(i, recentOnesTableBody.children[i].textContent);
                  }
                }

                // Show Global Pop-up Notification for "5"s
                if (rollData.rolled_number === 5) {
                    console.log('Rolled a 5! Attempting to show auto-dismissing popup.');
                    showNotification(`${rollData.username} rolled a 5!`);
                }
                 // Show Global Pop-up Notification for "2"s
                if (rollData.rolled_number === 2) {
                    console.log('Rolled a 2! Attempting to show hand-closed popup.');
                    showHandCloseNotification(`${rollData.username} rolled a 2!`);
                }
            }
        };

        websocket.onclose = (event) => {
            console.log('WebSocket connection closed:', event.code, event.reason);
            // Możesz tutaj zaimplementować logikę ponownego łączenia
            // np. setTimeout(() => new WebSocket(...), 3000);
        };

        websocket.onerror = (error) => {
            console.error('WebSocket Error:', error);
            // Jeśli wystąpi błąd, onclose zazwyczaj też zostanie wywołany.
        };

    } else {
        console.log("User is not logged in. Game elements not present.");
    }
});

// --- Show Global Pop-up Notification (auto-dismissing) ---
function showNotification(message) {
    const notificationContainer = document.getElementById('notification-container');
    const notificationDiv = document.createElement('div');
    notificationDiv.classList.add('notification');
    notificationDiv.textContent = message;
    notificationContainer.appendChild(notificationDiv);

    setTimeout(() => {
        notificationDiv.remove();
    }, 4500);
}