// CareConnect Client Logic
document.addEventListener('DOMContentLoaded', () => {
  // Mobile Sidebar Toggle
  const toggleBtn = document.querySelector('.btn-mobile-toggle');
  const sidebar = document.querySelector('.app-sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }

  // Auto-dismiss alerts after 5s
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });

  // Modal Backdrop Close & ESC key support
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
    }
  });

  // Init Dashboard Charts if present
  initDashboardCharts();
});

// Modal Open/Close helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    const firstInput = modal.querySelector('input:not([type=hidden]), select, textarea');
    if (firstInput) firstInput.focus();
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

// Edit Patient Form Population
function openEditPatientModal(btn) {
  const form = document.getElementById('editPatientForm');
  const id = btn.getAttribute('data-id');
  form.action = `/patients/edit/${id}`;
  
  document.getElementById('edit_patient_id_display').innerText = id;
  document.getElementById('edit_name').value = btn.getAttribute('data-name') || '';
  document.getElementById('edit_age').value = btn.getAttribute('data-age') || '';
  document.getElementById('edit_gender').value = btn.getAttribute('data-gender') || 'Male';
  document.getElementById('edit_phone').value = btn.getAttribute('data-phone') || '';
  document.getElementById('edit_blood_group').value = btn.getAttribute('data-blood-group') || 'O+';
  document.getElementById('edit_address').value = btn.getAttribute('data-address') || '';
  document.getElementById('edit_emergency_contact').value = btn.getAttribute('data-emergency-contact') || '';
  
  openModal('editPatientModal');
}

// Delete Confirmation Modal
function confirmDeletePatient(id, name) {
  const form = document.getElementById('deletePatientForm');
  form.action = `/patients/delete/${id}`;
  document.getElementById('delete_patient_name').innerText = `${name} (${id})`;
  openModal('deletePatientModal');
}

// Quick Book Appointment for Patient
function quickBookForPatient(id, name) {
  const select = document.getElementById('book_patient_id');
  if (select) {
    select.value = id;
  }
  const nameInput = document.getElementById('book_patient_name');
  if (nameInput) {
    nameInput.value = name;
  }
  openModal('bookAppointmentModal');
}

// Status update auto-submit for selects
function submitStatusForm(selectEl) {
  selectEl.closest('form').submit();
}

// Render Dashboard Charts with Chart.js
function initDashboardCharts() {
  const apptCanvas = document.getElementById('appointmentsChart');
  const bloodCanvas = document.getElementById('bloodChart');

  if (!apptCanvas && !bloodCanvas) return;

  fetch('/api/stats')
    .then(res => res.json())
    .then(data => {
      // Appointments Chart
      if (apptCanvas) {
        new Chart(apptCanvas, {
          type: 'doughnut',
          data: {
            labels: ['Scheduled', 'Completed', 'Cancelled'],
            datasets: [{
              data: [
                data.appointments.Scheduled || 0,
                data.appointments.Completed || 0,
                data.appointments.Cancelled || 0
              ],
              backgroundColor: ['#6366f1', '#10b981', '#94a3b8'],
              borderWidth: 2,
              borderColor: '#ffffff'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'bottom' }
            }
          }
        });
      }

      // Blood Demands Chart
      if (bloodCanvas) {
        const bloodLabels = Object.keys(data.blood_demand);
        const bloodValues = Object.values(data.blood_demand);
        new Chart(bloodCanvas, {
          type: 'bar',
          data: {
            labels: bloodLabels,
            datasets: [{
              label: 'Units Required',
              data: bloodValues,
              backgroundColor: '#e11d48',
              borderRadius: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: { beginAtZero: true, ticks: { stepSize: 1 } }
            },
            plugins: {
              legend: { display: false }
            }
          }
        });
      }
    })
    .catch(err => console.error('Failed to load chart metrics:', err));
}
