document.addEventListener('DOMContentLoaded', function() {
    // Check authentication state - redirect to login if not authenticated
    if (!auth.isLoggedIn()) {
        window.location.href = '/static/login.html';
        return;
    }
    
    // Show calendar container if authenticated
    document.getElementById('calendarContainer').style.display = 'block';

    // Track current event being edited
    let currentEventId = null;
    let timeChart = null;

    // Initialize FullCalendar
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: function(fetchInfo, successCallback, failureCallback) {
            fetch('/events/', {
                method: 'GET',
                headers: auth.getAuthHeaders()
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch events');
                }
                return response.json();
            })
            .then(events => {
                console.log('Loaded events:', events);
                successCallback(events);
                setTimeout(() => updateSummary(calendar.view.type), 100); // Update summary after events load
            })
            .catch(error => {
                console.error('Error loading events:', error);
                failureCallback(error);
            });
        },
        editable: true,
        selectable: true,
        // Handle clicks on dates
        dateClick: function(info) {
            if (info.view.type === 'dayGridMonth') {
                // In month view, switch to week view of the clicked date
                calendar.changeView('timeGridWeek', info.date);
            } else if (info.view.type === 'timeGridWeek' || info.view.type === 'timeGridDay') {
                // Reset for new event
                currentEventId = null;
                
                // Clear form first
                document.getElementById('eventTitle').value = '';
                document.getElementById('eventDescription').value = '';
                selectedTags.clear();
                updateTagsDisplay();
                document.querySelectorAll('.tag-btn').forEach(btn => btn.classList.remove('active'));
                
                // Hide delete button for new events
                document.getElementById('deleteEvent').style.display = 'none';
                document.getElementById('saveEvent').textContent = 'Save Event';
                
                // In week/day view, open event modal with the clicked date and time
                const dateOnly = info.dateStr.split('T')[0]; // Extract just the date part
                document.getElementById('eventStartDate').value = dateOnly;
                document.getElementById('eventEndDate').value = dateOnly; // Default to same day
                document.getElementById('eventStartTime').value = info.date.toTimeString().slice(0,5);
                
                // Calculate end time (1 hour after start time)
                const endTime = new Date(info.date);
                endTime.setHours(endTime.getHours() + 1);
                document.getElementById('eventEndTime').value = endTime.toTimeString().slice(0,5);
                
                var modal = new bootstrap.Modal(document.getElementById('eventModal'));
                modal.show();
            }
        },
        // Configuration for better interaction
        navLinks: true, // Enable clicking on day/week numbers
        nowIndicator: true, // Show current time indicator
        dayMaxEvents: true, // Allow "more" link when too many events
        // Customize the view switching animations
        viewDidMount: function(info) {
            info.el.style.opacity = '0';
            setTimeout(function() {
                info.el.style.opacity = '1';
            }, 0);
            
            // Update the summary based on the current view
            updateViewSummary(info.view.type);
        },
        // Update summary when date range changes (navigation arrows)
        datesSet: function(info) {
            updateSummary(info.view.type);
        },
        // Handle event clicks
        eventClick: function(info) {
            if (!auth.isLoggedIn()) {
                alert('Please log in to view event details');
                return;
            }

            const event = info.event;
            currentEventId = event.id; // Track which event we're editing
            
            document.getElementById('eventTitle').value = event.title;
            document.getElementById('eventStartDate').value = event.start ? event.start.toISOString().split('T')[0] : '';
            document.getElementById('eventStartTime').value = event.start ? event.start.toTimeString().slice(0,5) : '';
            document.getElementById('eventEndDate').value = event.end ? event.end.toISOString().split('T')[0] : '';
            document.getElementById('eventEndTime').value = event.end ? event.end.toTimeString().slice(0,5) : '';
            document.getElementById('eventDescription').value = event.extendedProps.description || '';
            
            // Load existing tags
            selectedTags.clear();
            document.querySelectorAll('.tag-btn').forEach(btn => btn.classList.remove('active'));
            
            if (event.extendedProps.tags) {
                const tags = event.extendedProps.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
                tags.forEach(tag => {
                    selectedTags.add(tag);
                    // Activate preset buttons if they match
                    const presetBtn = document.querySelector(`[data-tag="${tag}"]`);
                    if (presetBtn) {
                        presetBtn.classList.add('active');
                    }
                });
            }
            updateTagsDisplay();
            
            // Show delete button for existing events
            document.getElementById('deleteEvent').style.display = 'inline-block';
            document.getElementById('saveEvent').textContent = 'Update Event';
            
            var modal = new bootstrap.Modal(document.getElementById('eventModal'));
            modal.show();
        }
    });
    calendar.render();
    
    // Function to update summary when view changes
    function updateViewSummary(viewType) {
        updateSummary(viewType);
    }

    // Function to calculate event duration in hours
    function getEventDuration(event) {
        if (!event.start || !event.end) return 0;
        const start = new Date(event.start);
        const end = new Date(event.end);
        return (end - start) / (1000 * 60 * 60); // Convert to hours
    }

    // Function to check if event is in date range
    function isEventInRange(event, startDate, endDate) {
        if (!event.start) return false;
        const eventDate = new Date(event.start);
        return eventDate >= startDate && eventDate <= endDate;
    }

    // Function to calculate total available hours for the period
    function getTotalAvailableHours(viewType, startDate, endDate) {
        if (viewType === 'timeGridDay') {
            return 24; // 24 hours in a day
        } else if (viewType === 'timeGridWeek') {
            return 7 * 24; // 7 days * 24 hours
        } else if (viewType === 'dayGridMonth') {
            const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
            return days * 24; // Total days * 24 hours
        }
        return 0;
    }

    // Function to update summary based on current view
    function updateSummary(viewType) {
        const view = calendar.view;
        const startDate = new Date(view.activeStart);
        const endDate = new Date(view.activeEnd);
        
        let title;
        if (viewType === 'dayGridMonth') {
            title = 'Monthly Summary';
        } else if (viewType === 'timeGridWeek') {
            title = 'Weekly Summary';
        } else if (viewType === 'timeGridDay') {
            title = 'Daily Summary';
        }
        
        document.getElementById('summaryTitle').textContent = title;
        
        const events = calendar.getEvents();
        const tagHours = {};
        let totalScheduledHours = 0;
        
        events.forEach(event => {
            if (isEventInRange(event, startDate, endDate)) {
                const duration = getEventDuration(event);
                totalScheduledHours += duration;
                
                const tags = event.extendedProps.tags;
                if (tags && duration > 0) {
                    const tagList = tags.split(',').map(tag => tag.trim()).filter(tag => tag);
                    tagList.forEach(tag => {
                        tagHours[tag] = (tagHours[tag] || 0) + duration;
                    });
                }
            }
        });
        
        // Calculate unscheduled hours
        const totalAvailableHours = getTotalAvailableHours(viewType, startDate, endDate);
        const unscheduledHours = totalAvailableHours - totalScheduledHours;
        
        displaySummary(tagHours, unscheduledHours);
    }

    // Function to generate vibrant color for custom tags
    function getCustomTagColor(tag) {
        const vibrantColors = [
            '#e91e63', // Pink
            '#9c27b0', // Purple
            '#673ab7', // Deep Purple
            '#3f51b5', // Indigo
            '#2196f3', // Blue
            '#00bcd4', // Cyan
            '#009688', // Teal
            '#4caf50', // Green
            '#8bc34a', // Light Green
            '#cddc39', // Lime
            '#ffeb3b', // Yellow
            '#ff9800', // Orange
            '#ff5722', // Deep Orange
            '#795548', // Brown
            '#607d8b'  // Blue Grey
        ];
        
        // Generate consistent color based on tag name
        let hash = 0;
        for (let i = 0; i < tag.length; i++) {
            hash = tag.charCodeAt(i) + ((hash << 5) - hash);
        }
        const index = Math.abs(hash) % vibrantColors.length;
        return vibrantColors[index];
    }

    // Function to display the summary
    function displaySummary(tagHours, unscheduledHours) {
        const summaryDiv = document.getElementById('tagSummary');
        
        let html = '';
        const tagColors = {
            'productivity': '#0d6efd', // Bootstrap primary blue
            'recreation': '#198754',   // Bootstrap success green
            'personal': '#0dcaf0',     // Bootstrap info cyan
            'athletics': '#ffc107'     // Bootstrap warning yellow
        };
        
        const bootstrapColors = {
            'productivity': 'primary',
            'recreation': 'success', 
            'personal': 'info',
            'athletics': 'warning'
        };
        
        // Show scheduled tag hours
        if (Object.keys(tagHours).length > 0) {
            Object.entries(tagHours)
                .sort(([,a], [,b]) => b - a) // Sort by hours descending
                .forEach(([tag, hours]) => {
                    const bootstrapColor = bootstrapColors[tag.toLowerCase()];
                    const roundedHours = Math.round(hours * 10) / 10; // Round to 1 decimal
                    
                    if (bootstrapColor) {
                        // Use Bootstrap class for preset tags
                        html += `
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="badge bg-${bootstrapColor}">${tag}</span>
                                <span class="fw-bold">${roundedHours}h</span>
                            </div>
                        `;
                    } else {
                        // Use custom color for custom tags
                        const customColor = getCustomTagColor(tag);
                        html += `
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="badge" style="background-color: ${customColor}; color: white;">${tag}</span>
                                <span class="fw-bold">${roundedHours}h</span>
                            </div>
                        `;
                    }
                });
        }
        
        // Show unscheduled hours
        if (unscheduledHours > 0) {
            const roundedUnscheduled = Math.round(unscheduledHours * 10) / 10;
            html += `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="badge bg-light text-dark">Unscheduled</span>
                    <span class="fw-bold text-muted">${roundedUnscheduled}h</span>
                </div>
            `;
        }
        
        if (html === '') {
            summaryDiv.innerHTML = '<p class="text-muted">No time data available</p>';
        } else {
            summaryDiv.innerHTML = html;
        }
        
        // Create pie chart
        createPieChart(tagHours, unscheduledHours, tagColors);
    }

    // Function to create pie chart
    function createPieChart(tagHours, unscheduledHours, tagColors) {
        const ctx = document.getElementById('timeChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (timeChart) {
            timeChart.destroy();
        }
        
        const labels = [];
        const data = [];
        const colors = [];
        
        // Add tag data
        Object.entries(tagHours).forEach(([tag, hours]) => {
            labels.push(tag.charAt(0).toUpperCase() + tag.slice(1));
            data.push(Math.round(hours * 10) / 10);
            const color = tagColors[tag.toLowerCase()] || getCustomTagColor(tag);
            colors.push(color);
        });
        
        // Calculate and display unscheduled percentage
        const totalScheduledHours = data.reduce((sum, hours) => sum + hours, 0);
        const totalHours = totalScheduledHours + unscheduledHours;
        const unscheduledPercent = totalHours > 0 ? ((unscheduledHours / totalHours) * 100).toFixed(1) : 0;
        
        document.getElementById('unscheduledPercent').textContent = 
            unscheduledHours > 0 ? `${unscheduledPercent}% Unscheduled` : '';
        
        // Only create chart if there's data
        if (data.length > 0) {
            timeChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: colors,
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false // Hide legend since we show it above
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((context.parsed / total) * 100).toFixed(1);
                                    return `${context.label}: ${context.parsed}h (${percentage}%)`;
                                }
                            }
                        }
                    },
                    animation: {
                        duration: 0 // Disable animations to prevent resize issues
                    }
                }
            });
        }
    }



    // Handle save event button click
    document.getElementById('saveEvent').addEventListener('click', function() {
        if (!auth.isLoggedIn()) {
            alert('Please log in to save events');
            return;
        }

        const title = document.getElementById('eventTitle').value;
        const startDate = document.getElementById('eventStartDate').value;
        const startTime = document.getElementById('eventStartTime').value;
        const endDate = document.getElementById('eventEndDate').value;
        const endTime = document.getElementById('eventEndTime').value;
        const description = document.getElementById('eventDescription').value;
        const tags = document.getElementById('eventTags').value;

        if (!title || !startDate) {
            alert('Please fill in at least the title and start date!');
            return;
        }

        const event = {
            id: currentEventId || Date.now().toString(), // Use existing ID or generate new
            title: title,
            start: startTime ? `${startDate}T${startTime}` : startDate,
            end: endDate && endTime ? `${endDate}T${endTime}` : (endDate ? endDate : null),
            description: description,
            tags: tags
        };

        fetch('/events/', {
            method: 'POST',
            headers: auth.getAuthHeaders(),
            body: JSON.stringify(event)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to save event');
            }
            return response.json();
        })
        .then(result => {
            calendar.refetchEvents();
            setTimeout(() => updateSummary(calendar.view.type), 100); // Update summary after events load
            var modal = bootstrap.Modal.getInstance(document.getElementById('eventModal'));
            modal.hide();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to save event. Please try again.');
        });
    });

    // Tag management functionality
    let selectedTags = new Set();

    function updateTagsDisplay() {
        const tagsContainer = document.getElementById('selectedTags');
        const hiddenInput = document.getElementById('eventTags');
        
        tagsContainer.innerHTML = '';
        
        selectedTags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'badge bg-primary me-1 mb-1';
            tagElement.innerHTML = `${tag} <button type="button" class="btn-close btn-close-white" style="font-size: 0.7em;" onclick="removeTag('${tag}')"></button>`;
            tagsContainer.appendChild(tagElement);
        });
        
        hiddenInput.value = Array.from(selectedTags).join(', ');
    }

    function addTag(tag) {
        if (tag && tag.trim()) {
            selectedTags.add(tag.trim());
            updateTagsDisplay();
        }
    }

    window.removeTag = function(tag) {
        selectedTags.delete(tag);
        updateTagsDisplay();
    }

    // Handle preset tag buttons
    document.querySelectorAll('.tag-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tag = this.getAttribute('data-tag');
            if (selectedTags.has(tag)) {
                selectedTags.delete(tag);
                this.classList.remove('active');
            } else {
                selectedTags.add(tag);
                this.classList.add('active');
            }
            updateTagsDisplay();
        });
    });

    // Handle custom tag input
    document.getElementById('addCustomTag').addEventListener('click', function() {
        const input = document.getElementById('customTag');
        const tag = input.value.trim();
        if (tag) {
            addTag(tag);
            input.value = '';
        }
    });

    // Handle Enter key in custom tag input
    document.getElementById('customTag').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('addCustomTag').click();
        }
    });

    // Handle time adjustment buttons
    function adjustTime(inputId, minutes) {
        const input = document.getElementById(inputId);
        if (!input.value) {
            input.value = '09:00'; // Default time if empty
        }
        
        const [hours, mins] = input.value.split(':').map(Number);
        const totalMinutes = hours * 60 + mins + minutes;
        
        // Handle day overflow/underflow
        const newHours = Math.floor((totalMinutes % (24 * 60)) / 60);
        const newMins = totalMinutes % 60;
        
        // Ensure positive values
        const finalHours = newHours < 0 ? 24 + newHours : newHours;
        const finalMins = newMins < 0 ? 60 + newMins : newMins;
        
        input.value = `${String(finalHours).padStart(2, '0')}:${String(finalMins).padStart(2, '0')}`;
    }

    // Add event listeners to time adjustment buttons
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            const action = this.getAttribute('data-action');
            const minutes = action === 'increase' ? 15 : -15;
            adjustTime(target, minutes);
        });
    });

    // Handle delete event button click
    document.getElementById('deleteEvent').addEventListener('click', function() {
        if (!currentEventId) return;
        
        if (confirm('Are you sure you want to delete this event?')) {
            fetch(`/events/${currentEventId}`, {
                method: 'DELETE',
                headers: auth.getAuthHeaders()
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to delete event');
                }
                calendar.refetchEvents();
                setTimeout(() => updateSummary(calendar.view.type), 100); // Update summary after events load
                var modal = bootstrap.Modal.getInstance(document.getElementById('eventModal'));
                modal.hide();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to delete event. Please try again.');
            });
        }
    });

    // Handle logout
    document.getElementById('logoutButton').addEventListener('click', function() {
        auth.logout();
        window.location.href = '/static/login.html';
    });

    // Handle file upload
    const uploadForm = document.getElementById('uploadForm');
    const uploadStatus = document.getElementById('uploadStatus');

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!auth.isLoggedIn()) {
            alert('Please log in to upload files');
            return;
        }
        
        const fileInput = document.getElementById('imageFile');
        if (!fileInput.files[0]) {
            uploadStatus.innerHTML = 'Please select a file';
            uploadStatus.className = 'error';
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            uploadStatus.innerHTML = 'Uploading and processing image...';
            uploadStatus.className = '';
            
            const response = await fetch('/uploadfile/', {
                method: 'POST',
                headers: auth.getAuthHeaders(),
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                uploadStatus.innerHTML = result.message || 'File uploaded successfully!';
                uploadStatus.className = 'success';
                calendar.refetchEvents();
                fileInput.value = '';
            } else {
                throw new Error(result.detail || 'Upload failed');
            }
        } catch (error) {
            uploadStatus.innerHTML = 'Error: ' + error.message;
            uploadStatus.className = 'error';
        }
    });
});