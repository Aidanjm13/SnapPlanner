document.addEventListener('DOMContentLoaded', function() {
    // Initialize FullCalendar
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: '/events/',  // Fetch events from our API
        editable: true,
        selectable: true,
        // Handle clicks on dates
        dateClick: function(info) {
            if (info.view.type === 'dayGridMonth') {
                // In month view, switch to week view of the clicked date
                calendar.changeView('timeGridWeek', info.date);
            } else if (info.view.type === 'timeGridWeek' || info.view.type === 'timeGridDay') {
                // Only allow event creation in week or day view
                document.getElementById('eventDate').value = info.dateStr;
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
            
            // Update the add event button visibility based on the current view
            updateAddEventButtonVisibility(info.view.type);
        },
        // Handle event clicks
        eventClick: function(info) {
            // Show event details
            const event = info.event;
            document.getElementById('eventTitle').value = event.title;
            document.getElementById('eventDate').value = event.start ? event.start.toISOString().split('T')[0] : '';
            document.getElementById('eventStartTime').value = event.start ? event.start.toTimeString().slice(0,5) : '';
            document.getElementById('eventEndTime').value = event.end ? event.end.toTimeString().slice(0,5) : '';
            document.getElementById('eventDescription').value = event.extendedProps.description || '';
            
            var modal = new bootstrap.Modal(document.getElementById('eventModal'));
            modal.show();
        }
    });
    calendar.render();
    
    // Function to update add event button visibility
    function updateAddEventButtonVisibility(viewType) {
        const addEventHint = document.getElementById('addEventHint');
        if (viewType === 'dayGridMonth') {
            addEventHint.textContent = 'Click on a day to view its week';
            addEventHint.style.color = '#666';
        } else {
            addEventHint.textContent = 'Click anywhere on the calendar to add an event';
            addEventHint.style.color = '#28a745';
        }
    }

    // Handle save event button click
    document.getElementById('saveEvent').addEventListener('click', function() {
        const title = document.getElementById('eventTitle').value;
        const date = document.getElementById('eventDate').value;
        const startTime = document.getElementById('eventStartTime').value;
        const endTime = document.getElementById('eventEndTime').value;
        const description = document.getElementById('eventDescription').value;

        if (!title || !date) {
            alert('Please fill in at least the title and date!');
            return;
        }

        // Create event object
        const event = {
            title: title,
            start: startTime ? `${date}T${startTime}` : date,
            end: endTime ? `${date}T${endTime}` : null,
            description: description
        };

        // Send to server
        fetch('/events/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(event)
        })
        .then(response => response.json())
        .then(data => {
            // Close modal
            var modal = bootstrap.Modal.getInstance(document.getElementById('eventModal'));
            modal.hide();
            
            // Clear form
            document.getElementById('eventForm').reset();
            
            // Refresh calendar
            calendar.refetchEvents();
            
            // Show success message
            alert('Event created successfully!');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error creating event: ' + error.message);
        });
    });

    // Handle file upload
    const uploadForm = document.getElementById('uploadForm');
    const uploadStatus = document.getElementById('uploadStatus');

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData();
        const fileInput = document.getElementById('imageFile');
        formData.append('file', fileInput.files[0]);

        try {
            uploadStatus.innerHTML = 'Uploading and processing image...';
            uploadStatus.className = '';
            
            const response = await fetch('/uploadfile/', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                uploadStatus.innerHTML = 'File uploaded successfully! Processing events...';
                uploadStatus.className = 'success';
                
                // Refresh calendar events
                calendar.refetchEvents();
            } else {
                throw new Error(result.detail || 'Upload failed');
            }
        } catch (error) {
            uploadStatus.innerHTML = 'Error: ' + error.message;
            uploadStatus.className = 'error';
        }
    });
});