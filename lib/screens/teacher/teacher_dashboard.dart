import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:intl/intl.dart';
import '../../providers/auth_provider.dart';
import '../../providers/session_provider.dart';

class TeacherDashboard extends StatefulWidget {
  const TeacherDashboard({super.key});

  @override
  State<TeacherDashboard> createState() => _TeacherDashboardState();
}

class _TeacherDashboardState extends State<TeacherDashboard> {
  final _subjectController = TextEditingController();
  final _classNameController = TextEditingController();

  Future<void> _showCreateSessionModal(BuildContext context) async {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1A1A2E),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
          left: 24,
          right: 24,
          top: 24,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'New Attendance Session',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: _subjectController,
              decoration: const InputDecoration(hintText: 'Subject (e.g., Mathematics)'),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _classNameController,
              decoration: const InputDecoration(hintText: 'Class/Section (e.g., CS-A)'),
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () async {
                if (_subjectController.text.isNotEmpty && _classNameController.text.isNotEmpty) {
                  final success = await context.read<SessionProvider>().createSession(
                    _subjectController.text,
                    _classNameController.text,
                  );
                  if (success) {
                    Navigator.pop(context);
                  }
                }
              },
              child: const Text('Start Session'),
            ),
            const SizedBox(height: 48),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final session = context.watch<SessionProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Teacher Dashboard'),
        actions: [
          IconButton(
            onPressed: () => auth.logout(),
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: const Color(0xFF6C63FF),
                  child: Text(
                    auth.name.isNotEmpty ? auth.name[0] : 'T',
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                ),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Welcome,',
                      style: TextStyle(color: Colors.grey.shade400, fontSize: 14),
                    ),
                    Text(
                      auth.name,
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 32),
            
            if (!session.hasActiveSession)
              _buildEmptyState(context)
            else
              _buildActiveSession(context, session),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          children: [
            const Icon(Icons.event_note, size: 64, color: Color(0xFF6C63FF)),
            const SizedBox(height: 16),
            const Text(
              'No Active Session',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              'Create a session to start taking attendance.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey.shade400),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => _showCreateSessionModal(context),
              icon: const Icon(Icons.add),
              label: const Text('Create Session'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActiveSession(BuildContext context, SessionProvider session) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                Text(
                  session.currentSession!['subject'],
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                ),
                Text(
                  'Class: ${session.currentSession!['class']}',
                  style: TextStyle(color: Colors.grey.shade400),
                ),
                const SizedBox(height: 24),
                if (session.qrData.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: QrImageView(
                      data: session.qrData,
                      version: QrVersions.auto,
                      size: 200.0,
                    ),
                  )
                else
                  const SizedBox(
                    height: 200,
                    child: Center(child: CircularProgressIndicator()),
                  ),
                const SizedBox(height: 24),
                const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.refresh, size: 16, color: Colors.blueAccent),
                    SizedBox(width: 8),
                    Text(
                      'Refreshing every 30s',
                      style: TextStyle(color: Colors.blueAccent, fontSize: 12),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _buildStat('Present', session.presentCount.toString()),
                    ElevatedButton(
                      onPressed: () => session.endSession(),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.redAccent,
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      ),
                      child: const Text('End Session', style: TextStyle(fontSize: 14)),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 32),
        const Text(
          'Live Attendance List',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        if (session.attendanceList.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 32),
            child: Center(child: Text('No students marked yet.')),
          )
        else
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: session.attendanceList.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final student = session.attendanceList[index];
              return ListTile(
                leading: CircleAvatar(
                  backgroundColor: Colors.greenAccent.withOpacity(0.1),
                  child: const Icon(Icons.check, color: Colors.greenAccent),
                ),
                title: Text(student['student_name']),
                subtitle: Text(student['student_id']),
                trailing: Text(
                  DateFormat.jm().format(DateTime.parse(student['timestamp'])),
                  style: const TextStyle(fontSize: 12),
                ),
                tileColor: const Color(0xFF1A1A2E),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              );
            },
          ),
      ],
    );
  }

  Widget _buildStat(String label, String value) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.greenAccent),
        ),
        Text(
          label,
          style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
        ),
      ],
    );
  }
}
