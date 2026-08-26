import { Ionicons } from '@expo/vector-icons';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

import {
  ApplicationsScreen,
  HomeScreen,
  JobsScreen,
  ProfileScreen,
} from '../screens/main';
import { colors, fontSize } from '../constants/theme';
import { MainTabParamList } from './types';

const Tab = createBottomTabNavigator<MainTabParamList>();

const tabIcons = {
  Home: ['home', 'home-outline'],
  Jobs: ['briefcase', 'briefcase-outline'],
  Applications: ['document-text', 'document-text-outline'],
  Profile: ['person', 'person-outline'],
} as const;

export function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarHideOnKeyboard: true,
        tabBarLabelStyle: { fontSize: fontSize.sm - 1 },
        tabBarStyle: {
          height: 60,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarIcon: ({ focused, color, size }) => (
          <Ionicons
            name={focused ? tabIcons[route.name][0] : tabIcons[route.name][1]}
            size={size}
            color={color}
          />
        ),
      })}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{ tabBarLabel: 'Home' }}
      />
      <Tab.Screen
        name="Jobs"
        component={JobsScreen}
        options={{ tabBarLabel: 'Jobs' }}
      />
      <Tab.Screen
        name="Applications"
        component={ApplicationsScreen}
        options={{ tabBarLabel: 'Applications' }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ tabBarLabel: 'Profile' }}
      />
    </Tab.Navigator>
  );
}
