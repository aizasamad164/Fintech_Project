import type { CapacitorConfig } from '@capacitor/cli';

// NFR-4.2: identical feature functionality across Desktop Web, iOS, and Android.
const config: CapacitorConfig = {
  appId: 'com.yourcompany.portfolioapp',
  appName: 'Portfolio App',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
  },
};

export default config;
