import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { Line, Bar } from 'react-chartjs-2';
import HeatMap from 'react-heatmap-grid';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { openDB } from 'idb';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend);

function App() {
  const { t, i18n } = useTranslation();
  const [theme, setTheme] = useState('light');
  const [userId, setUserId] = useState('');
  const [status, setStatus] = useState('');
  const [attendanceData, setAttendanceData] = useState([]);
  const [reservationData, setReservationData] = useState([]);
  const [accessLogs, setAccessLogs] = useState([]);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [weeklyReservations, setWeeklyReservations] = useState({});
  const [selectedMenu, setSelectedMenu] = useState(null);
  const [optOutTracking, setOptOutTracking] = useState(false);

  // Offline DB
  useEffect(() => {
    const initDB = async () => {
      const db = await openDB('attendance-db', 1, {
        upgrade(db) {
          db.createObjectStore('attendances', { keyPath: 'id' });
          db.createObjectStore('reservations', { keyPath: 'id' });
        },
      });
      return db;
    };
    initDB();
  }, []);

  // Sync offline data
  const syncOfflineData = async () => {
    const db = await openDB('attendance-db', 1);
    let tx = db.transaction('attendances', 'readwrite');
    let store = tx.objectStore('attendances');
    let offlineRecords = await store.getAll();
    for (const record of offlineRecords) {
      try {
        await axios.post('http://localhost/api/attendance/attendance/', record);
        await store.delete(record.id);
      } catch (error) {
        console.error('Sync failed:', error);
      }
    }
    tx = db.transaction('reservations', 'readwrite');
    store = tx.objectStore('reservations');
    offlineRecords = await store.getAll();
    for (const record of offlineRecords) {
      try {
        await axios.post('http://localhost/api/catering/reservations/', record);
        await store.delete(record.id);
      } catch (error) {
        console.error('Sync failed:', error);
      }
    }
  };

  // Network status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      syncOfflineData();
    };
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Voice commands
  useEffect(() => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = i18n.language === 'fa' ? 'fa-IR' : i18n.language === 'ar' ? 'ar-SA' : 'en-US';
    recognition.onresult = (event) => {
      const command = event.results[0][0].transcript.toLowerCase();
      if (command.includes('record attendance')) {
        recordAttendance();
      } else if (command.includes('reserve food')) {
        reserveFood();
      }
    };
    recognition.start();
    return () => recognition.stop();
  }, [i18n.language]);

  // Fetch data
  useEffect(() => {
    axios.get('http://localhost/api/attendance/attendances').then(res => setAttendanceData(res.data)).catch(() => setAttendanceData([]));
    axios.get('http://localhost/api/catering/reservations').then(res => setReservationData(res.data)).catch(() => setReservationData([]));
    axios.get('http://localhost/api/access-control/access-logs').then(res => setAccessLogs(res.data)).catch(() => setAccessLogs([]));
    // Fetch recommended menu
    if (userId) {
      axios.get(`http://localhost/api/catering/recommend-menu/${userId}`).then(res => setSelectedMenu(res.data.menu_id));
    }
  }, [userId]);

  // Record attendance
  const recordAttendance = async () => {
    const record = { user_id: parseInt(userId), is_entry: true, id: Date.now() };
    if (!isOnline) {
      const db = await openDB('attendance-db', 1);
      const tx = db.transaction('attendances', 'readwrite');
      await tx.objectStore('attendances').add(record);
      setStatus('Stored offline');
      return;
    }
    try {
      const response = await axios.post('http://localhost/api/attendance/attendance/', record);
      setStatus(response.data.status);
    } catch (error) {
      setStatus('Error');
    }
  };

  // Reserve food
  const reserveFood = async (date, menuId, quantity) => {
    const record = { user_id: parseInt(userId), menu_id: menuId || selectedMenu, quantity: quantity || 1, date, is_guest: false, id: Date.now() };
    if (!isOnline) {
      const db = await openDB('attendance-db', 1);
      const tx = db.transaction('reservations', 'readwrite');
      await tx.objectStore('reservations').add(record);
      setStatus('Stored offline');
      return;
    }
    try {
      const response = await axios.post('http://localhost/api/catering/reservations/', record);
      setStatus('Reserved');
      setWeeklyReservations(prev => ({ ...prev, [date]: { menu_id: menuId, quantity } }));
    } catch (error) {
      setStatus('Error');
    }
  };

  // Toggle opt-out
  const toggleOptOut = () => {
    setOptOutTracking(!optOutTracking);
    if (optOutTracking) {
      // Resume tracking
    } else {
      // Stop tracking
    }
  };

  // Chart data
  const attendanceChartData = {
    labels: attendanceData.map(d => new Date(d.timestamp).toLocaleDateString()),
    datasets: [{ label: t('recentAttendance'), data: attendanceData.map(d => d.is_entry ? 1 : 0), borderColor: 'rgba(75, 192, 192, 1)', fill: false }]
  };

  const reservationChartData = {
    labels: reservationData.map(d => `Menu ${d.menu_id}`),
    datasets: [{ label: t('foodReservations'), data: reservationData.map(d => d.quantity), backgroundColor: 'rgba(153, 102, 255, 0.6)' }]
  };

  const consumptionTrendData = {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [{
      label: t('foodConsumption'),
      data: reservationData.reduce((acc, d) => {
        const week = Math.floor((new Date(d.date).getDate() - 1) / 7);
        acc[week] = (acc[week] || 0) + d.quantity;
        return acc;
      }, [0, 0, 0, 0]),
      backgroundColor: 'rgba(255, 159, 64, 0.6)'
    }]
  };

  // Heatmap data
  const xLabels = ['Parking', 'Room 1', 'Room 2', 'Canteen'];
  const yLabels = Array.from({ length: 24 }, (_, i) => `${i}:00`);
  const heatmapData = Array(24).fill().map(() => Array(4).fill(0));
  accessLogs.forEach(log => {
    if (!optOutTracking) {
      const hour = new Date(log.timestamp).getHours();
      const locationIndex = xLabels.indexOf(log.location);
      if (locationIndex !== -1) heatmapData[hour][locationIndex]++;
    }
  });

  // Weekly reservation calendar
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const today = new Date();
  const weekDates = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(today);
    date.setDate(today.getDate() + i);
    return date.toISOString().split('T')[0];
  });

  // Toggle theme
  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  // Change language
  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    document.documentElement.dir = lng === 'fa' || lng === 'ar' ? 'rtl' : 'ltr';
  };

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-900'}`}>
      {/* Sidebar */}
      <div className="fixed top-0 left-0 h-full w-64 bg-gray-800 text-white p-4">
        <h2 className="text-2xl font-bold mb-6">{t('dashboard')}</h2>
        <nav>
          <ul>
            <li className="mb-4"><a href="#attendance" className="hover:text-gray-300">{t('attendance')}</a></li>
            <li className="mb-4"><a href="#catering" className="hover:text-gray-300">{t('catering')}</a></li>
            <li className="mb-4"><a href="#accessControl" className="hover:text-gray-300">{t('accessControl')}</a></li>
          </ul>
        </nav>
        <div className="mt-8">
          <button onClick={() => changeLanguage('fa')} className="block mb-2 text-sm hover:text-gray-300" aria-label="Switch to Persian">فارسی</button>
          <button onClick={() => changeLanguage('en')} className="block mb-2 text-sm hover:text-gray-300" aria-label="Switch to English">English</button>
          <button onClick={() => changeLanguage('ar')} className="block mb-2 text-sm hover:text-gray-300" aria-label="Switch to Arabic">العربية</button>
          <button onClick={toggleTheme} className="mt-4 bg-blue-500 text-white p-2 rounded w-full" aria-label={theme === 'dark' ? t('lightMode') : t('darkMode')}>
            {theme === 'dark' ? t('lightMode') : t('darkMode')}
          </button>
          <button onClick={toggleOptOut} className="mt-4 bg-gray-500 text-white p-2 rounded w-full" aria-label={optOutTracking ? 'Enable Tracking' : 'Disable Tracking'}>
            {optOutTracking ? 'Enable Tracking' : 'Disable Tracking'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64 p-8">
        <h1 className="text-3xl font-bold mb-8">{t('dashboard')}</h1>

        {/* Attendance Section */}
        <section id="attendance" className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">{t('attendance')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-md dark:bg-gray-800">
              <h3 className="text-lg font-medium mb-4">{t('recordAttendance')}</h3>
              <label className="block text-sm mb-2" htmlFor="userId">{t('userId')}</label>
              <input
                id="userId"
                type="number"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="w-full p-2 border rounded dark:bg-gray-700 dark:text-white"
                aria-describedby="userIdHelp"
              />
              <p id="userIdHelp" className="text-sm text-gray-500 mt-1">شناسه کاربر را وارد کنید</p>
              <button
                onClick={recordAttendance}
                className="mt-4 bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
                aria-label={t('recordAttendance')}
              >
                {t('recordAttendance')}
              </button>
              {status && <p className="mt-4" aria-live="polite">{t('status')}: {status}</p>}
            </div>
            <div className="bg-white p-6 rounded-lg shadow-md dark:bg-gray-800">
              <h3 className="text-lg font-medium mb-4">{t('recentAttendance')}</h3>
              <Line data={attendanceChartData} options={{ responsive: true }} />
            </div>
          </div>
        </section>

        {/* Catering Section */}
        <section id="catering" className="mb-12">
          <h2 className="text-2xl font-semibold mb-4">{t('catering')}</h2>
          <div className="bg-white p-6 rounded-lg shadow-md dark:bg-gray-800">
            <h3 className="text-lg font-medium mb-4">{t('foodReservations')}</h3>
            <div className="mb-4">
              <h4 className="text-md font-medium mb-2">Weekly Reservations</h4>
              <div className="grid grid-cols-7 gap-2">
                {weekDates.map((date, i) => (
                  <div key={date} className="text-center">
                    <p>{days[new Date(date).getDay()]}</p>
                    <input
                      type="number"
                      min="0"
                      defaultValue={weeklyReservations[date]?.quantity || 0}
                      onChange={(e) => reserveFood(date, selectedMenu, parseInt(e.target.value))}
                      className="w-full p-1 border rounded dark:bg-gray-700 dark:text-white"
                      aria-label={`Reservation for ${date}`}
                    />
                  </div>
                ))}
              </div>
              <p className="mt-2 text-sm">Recommended Menu: {selectedMenu || 'Loading...'}</p>
            </div>
            <Bar data={reservationChartData} options={{ responsive: true }} />
            <h4 className="text-md font-medium mt-4 mb-2">Consumption Trends</h4>
            <Bar data={consumptionTrendData} options={{ responsive: true }} />
          </div>
        </section>

        {/* Access Control Section */}
        <section id="accessControl">
          <h2 className="text-2xl font-semibold mb-4">{t('accessControl')}</h2>
          <div className="bg-white p-6 rounded-lg shadow-md dark:bg-gray-800">
            <h3 className="text-lg font-medium mb-4">{t('accessLogs')}</h3>
            <HeatMap xLabels={xLabels} yLabels={yLabels} data={heatmapData} />
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;