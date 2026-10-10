//main.dart
import 'package:flutter/material.dart';
import 'screens/home_screen.dart';


void main() {
  runApp(const ParasolApp());
}

class ParasolApp extends StatelessWidget {
  const ParasolApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "Smart Parasol",
      debugShowCheckedModeBanner: false,
      home: const HomeScreen(),
    );
  }
}
