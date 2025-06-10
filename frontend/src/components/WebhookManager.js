import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  TextField,
  Typography,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, Edit as EditIcon, Send as SendIcon } from '@mui/icons-material';
import { apiService } from '../services/api';

const WebhookManager = () => {
  const [webhooks, setWebhooks] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    method: 'POST',
    headers: {},
    enabled: true,
    alertTypes: ['critical', 'warning', 'info']
  });

  useEffect(() => {
    fetchWebhooks();
  }, []);

  const fetchWebhooks = async () => {
    const { success, data } = await apiService.webhooks.getSubscriptions();
    if (success) {
      setWebhooks(data);
    }
  };

  const handleOpenDialog = (webhook = null) => {
    if (webhook) {
      setFormData(webhook);
      setSelectedWebhook(webhook);
    } else {
      setFormData({
        name: '',
        url: '',
        method: 'POST',
        headers: {},
        enabled: true,
        alertTypes: ['critical', 'warning', 'info']
      });
      setSelectedWebhook(null);
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedWebhook(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = selectedWebhook
      ? await apiService.webhooks.updateSubscription(selectedWebhook.id, formData)
      : await apiService.webhooks.createSubscription(formData);

    if (response.success) {
      setNotification({ 
        open: true, 
        message: response.message || `Webhook ${selectedWebhook ? 'updated' : 'created'} successfully`, 
        severity: 'success' 
      });
      handleCloseDialog();
      fetchWebhooks();
    } else {
      setNotification({ 
        open: true, 
        message: response.error || 'Error saving webhook', 
        severity: 'error' 
      });
    }
  };

  const handleDelete = async (id) => {
    const { success, message } = await apiService.webhooks.deleteSubscription(id);
    if (success) {
      setNotification({ open: true, message, severity: 'success' });
      fetchWebhooks();
    } else {
      setNotification({ open: true, message: 'Error deleting webhook', severity: 'error' });
    }
  };

  const handleTest = async (webhook) => {
    const { success, message } = await apiService.webhooks.testWebhook({
      url: webhook.url,
      method: webhook.method,
      headers: webhook.headers
    });

    setNotification({
      open: true,
      message: success ? 'Test notification sent successfully' : 'Error sending test notification',
      severity: success ? 'success' : 'error'
    });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">Webhook Subscriptions</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<SendIcon />}
            onClick={async () => {
              const response = await apiService.webhooks.testAllWebhooks();
              setNotification({
                open: true,
                message: response.success ? response.message : response.error,
                severity: response.success ? 'success' : 'error'
              });
            }}
          >
            Test All Webhooks
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Webhook
          </Button>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>URL</TableCell>
              <TableCell>Method</TableCell>
              <TableCell>Alert Types</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {webhooks.map((webhook) => (
              <TableRow key={webhook.id}>
                <TableCell>{webhook.name}</TableCell>
                <TableCell>{webhook.url}</TableCell>
                <TableCell>{webhook.method}</TableCell>
                <TableCell>
                  {webhook.alertTypes.map((type) => (
                    <Chip
                      key={type}
                      label={type}
                      size="small"
                      sx={{ mr: 0.5 }}
                      color={
                        type === 'critical' ? 'error' :
                        type === 'warning' ? 'warning' : 'info'
                      }
                    />
                  ))}
                </TableCell>
                <TableCell>
                  <Chip
                    label={webhook.enabled ? 'Active' : 'Inactive'}
                    color={webhook.enabled ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton onClick={() => handleOpenDialog(webhook)} size="small">
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleTest(webhook)} size="small">
                    <SendIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDelete(webhook.id)} size="small">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <form onSubmit={handleSubmit}>
          <DialogTitle>
            {selectedWebhook ? 'Edit Webhook' : 'Add Webhook'}
          </DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="URL"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Method"
              value={formData.method}
              onChange={(e) => setFormData({ ...formData, method: e.target.value })}
              margin="normal"
              required
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.enabled}
                  onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                />
              }
              label="Enabled"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button type="submit" variant="contained">Save</Button>
          </DialogActions>
        </form>
      </Dialog>

      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification({ ...notification, open: false })}
      >
        <Alert severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default WebhookManager; 