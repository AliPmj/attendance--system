import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      fa: {
        translation: {
          dashboard: "داشبورد",
          attendance: "حضور و غیاب",
          catering: "اتوماسیون تغذیه",
          accessControl: "کنترل تردد",
          switchLanguage: "تغییر زبان",
          recordAttendance: "ثبت حضور",
          userId: "شناسه کاربر",
          status: "وضعیت",
          recentAttendance: "حضورهای اخیر",
          foodReservations: "رزروهای غذا",
          accessLogs: "لاگ‌های تردد",
          darkMode: "حالت تاریک",
          lightMode: "حالت روشن"
        }
      },
      en: {
        translation: {
          dashboard: "Dashboard",
          attendance: "Attendance",
          catering: "Catering",
          accessControl: "Access Control",
          switchLanguage: "Switch Language",
          recordAttendance: "Record Attendance",
          userId: "User ID",
          status: "Status",
          recentAttendance: "Recent Attendance",
          foodReservations: "Food Reservations",
          accessLogs: "Access Logs",
          darkMode: "Dark Mode",
          lightMode: "Light Mode"
        }
      },
      ar: {
        translation: {
          dashboard: "لوحة القيادة",
          attendance: "الحضور والغياب",
          catering: "أتمتة الطعام",
          accessControl: "التحكم في الوصول",
          switchLanguage: "تغيير اللغة",
          recordAttendance: "تسجيل الحضور",
          userId: "معرف المستخدم",
          status: "الحالة",
          recentAttendance: "الحضور الأخير",
          foodReservations: "حجوزات الطعام",
          accessLogs: "سجلات الوصول",
          darkMode: "الوضع الداكن",
          lightMode: "الوضع الفاتح"
        }
      }
    },
    lng: 'fa',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;