import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'ba.popust.app',
  appName: 'Popust.ba',
  webDir: 'dist',
  server: {
    // For development - load from your dev server
    // url: 'http://localhost:3000',
    // cleartext: true,

    // For production - use the bundled app
    androidScheme: 'https'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#7c3aed',
      showSpinner: false
    },
    StatusBar: {
      style: 'light',
      backgroundColor: '#7c3aed'
    }
  },
  ios: {
    contentInset: 'automatic'
  },
  android: {
    allowMixedContent: true
  }
};

export default config;
