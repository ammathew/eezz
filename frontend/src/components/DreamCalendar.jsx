import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay, startOfMonth, endOfMonth } from 'date-fns';
import enUS from 'date-fns/locale/en-US';
import ReactMarkdown from 'react-markdown';
import {
  Box,
  Paper,
  Typography,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { chatApi } from '../services/chatApi';
import 'react-big-calendar/lib/css/react-big-calendar.css';

const locales = {
  'en-US': enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

const DreamCalendar = () => {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [dreamsData, setDreamsData] = useState({});
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedDateDreams, setSelectedDateDreams] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);

  // Fetch dreams for current month view
  useEffect(() => {
    const fetchDreams = async () => {
      setLoading(true);
      try {
        const start = startOfMonth(currentDate);
        const end = endOfMonth(currentDate);

        const startDate = format(start, 'yyyy-MM-dd');
        const endDate = format(end, 'yyyy-MM-dd');

        const data = await chatApi.getConversationsByDate(startDate, endDate);
        setDreamsData(data);
      } catch (error) {
        console.error('Failed to fetch calendar data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDreams();
  }, [currentDate]);

  // Convert dreams data to calendar events
  const events = useMemo(() => {
    const eventList = [];

    Object.entries(dreamsData).forEach(([dateStr, dreams]) => {
      dreams.forEach((dream) => {
        const date = parse(dateStr, 'yyyy-MM-dd', new Date());
        console.log('Dream data:', dream); // Debug: check what data we're getting
        eventList.push({
          id: dream.id,
          title: dream.title,
          start: date,
          end: date,
          allDay: true,
          resource: dream, // Store full dream data
        });
      });
    });

    return eventList;
  }, [dreamsData]);

  const handleSelectEvent = useCallback((event) => {
    // Navigate to chat with conversation ID as query param
    navigate(`/chat?conversationId=${event.id}`);
  }, [navigate]);

  const handleNavigate = useCallback((newDate) => {
    setCurrentDate(newDate);
  }, []);

  const handleShowMore = useCallback((events, date) => {
    // Extract the dreams from events
    const dreams = events.map(e => e.resource);
    setSelectedDateDreams(dreams);
    setSelectedDate(date);
    setDialogOpen(true);
  }, []);

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedDateDreams([]);
    setSelectedDate(null);
  };

  const handleDreamClick = (dreamId) => {
    handleCloseDialog();
    // Navigate to chat with conversation ID as query param
    navigate(`/chat?conversationId=${dreamId}`);
  };

  // Custom event renderer with tooltip
  const EventComponent = ({ event }) => {
    const messages = event.resource.messages || [];

    return (
      <Tooltip
        title={
          <Box sx={{ maxWidth: 500, maxHeight: 400, overflow: 'auto' }}>
            <Typography variant="body2" sx={{ fontWeight: 'bold', display: 'block', mb: 1 }}>
              {event.title}
            </Typography>
            {messages.length > 0 ? (
              <Box>
                {messages.map((msg, idx) => (
                  <Box
                    key={msg.id}
                    sx={{
                      mb: 1.5,
                      p: 1,
                      bgcolor: msg.role === 'user' ? 'rgba(233, 30, 99, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                      borderRadius: 1,
                      borderLeft: 3,
                      borderColor: msg.role === 'user' ? '#e91e63' : 'rgba(255, 255, 255, 0.3)',
                    }}
                  >
                    <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 0.5, textTransform: 'capitalize' }}>
                      {msg.role === 'user' ? 'You' : 'AI'}
                    </Typography>
                    <Box
                      sx={{
                        fontSize: '0.75rem',
                        '& p': { mb: 0.5 },
                        '& ul, & ol': { pl: 2, mb: 0.5 },
                        '& li': { mb: 0.25 },
                        '& h1, & h2, & h3, & h4, & h5, & h6': { mt: 0.75, mb: 0.5, fontWeight: 'bold' },
                        '& code': {
                          bgcolor: 'rgba(255, 255, 255, 0.1)',
                          px: 0.5,
                          py: 0.25,
                          borderRadius: 0.5,
                          fontSize: '0.85em',
                          fontFamily: 'monospace',
                        },
                        '& pre': {
                          bgcolor: 'rgba(0, 0, 0, 0.3)',
                          p: 1,
                          borderRadius: 1,
                          overflow: 'auto',
                          '& code': {
                            bgcolor: 'transparent',
                            p: 0,
                          },
                        },
                        '& strong': { fontWeight: 'bold' },
                        '& em': { fontStyle: 'italic' },
                        '& blockquote': {
                          borderLeft: 2,
                          borderColor: 'rgba(255, 255, 255, 0.2)',
                          pl: 1,
                          ml: 0,
                          fontStyle: 'italic',
                        },
                      }}
                    >
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </Box>
                  </Box>
                ))}
              </Box>
            ) : (
              <Typography variant="caption">No messages</Typography>
            )}
          </Box>
        }
        arrow
        placement="top"
        enterDelay={200}
        leaveDelay={200}
      >
        <Box
          sx={{
            height: '100%',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            px: 0.5,
          }}
        >
          {event.title}
        </Box>
      </Tooltip>
    );
  };

  return (
    <Box sx={{ p: 1.5, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      <Paper sx={{ p: 1.5, display: 'flex', flexDirection: 'column', maxWidth: 1400, margin: '0 auto', width: '100%' }}>
        <Box sx={{ height: '70vh', minHeight: 500 }}>
          <Calendar
            localizer={localizer}
            events={events}
            startAccessor="start"
            endAccessor="end"
            style={{ height: '100%' }}
            onSelectEvent={handleSelectEvent}
            onNavigate={handleNavigate}
            date={currentDate}
            views={['month']}
            defaultView="month"
            components={{
              event: EventComponent,
            }}
            onShowMore={handleShowMore}
            eventPropGetter={(event) => ({
              style: {
                backgroundColor: '#e91e63',
                borderRadius: '4px',
                opacity: 0.95,
                color: 'white',
                border: 'none',
                display: 'block',
                padding: '1px 4px',
                fontSize: '0.75rem',
                fontWeight: '500',
              },
            })}
            dayPropGetter={(date) => ({
              style: {
                backgroundColor: 'transparent',
              },
            })}
          />
        </Box>

        {/* Custom CSS for calendar styling */}
        <style>{`
          .rbc-calendar {
            font-family: inherit;
          }

          .rbc-header {
            padding: 6px 4px;
            font-weight: 600;
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.7);
            border-bottom: 1px solid rgba(255, 255, 255, 0.12);
          }

          .rbc-month-view {
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 8px;
            overflow: hidden;
            background: rgba(255, 255, 255, 0.02);
          }

          .rbc-month-row {
            border-color: rgba(255, 255, 255, 0.08);
            min-height: 60px;
          }

          .rbc-day-bg {
            border-color: rgba(255, 255, 255, 0.08);
          }

          .rbc-today {
            background-color: rgba(233, 30, 99, 0.1);
          }

          .rbc-off-range-bg {
            background-color: rgba(0, 0, 0, 0.2);
          }

          .rbc-date-cell {
            padding: 2px 4px;
            text-align: right;
          }

          .rbc-date-cell > a {
            font-size: 0.8rem;
          }

          .rbc-date-cell > a {
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
          }

          .rbc-off-range .rbc-date-cell > a {
            color: rgba(255, 255, 255, 0.3);
          }

          .rbc-toolbar {
            padding: 4px 0;
            margin-bottom: 8px;
            gap: 6px;
          }

          .rbc-toolbar button {
            color: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.23);
            background: transparent;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s;
            font-size: 0.875rem;
          }

          .rbc-toolbar button:hover {
            background-color: rgba(233, 30, 99, 0.2);
            border-color: #e91e63;
          }

          .rbc-toolbar button:active,
          .rbc-toolbar button.rbc-active {
            background-color: #e91e63;
            border-color: #e91e63;
            color: white;
          }

          .rbc-toolbar-label {
            font-size: 1.1rem;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.95);
          }

          .rbc-event {
            cursor: pointer;
            transition: all 0.2s;
          }

          .rbc-event:hover {
            opacity: 1 !important;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(233, 30, 99, 0.4);
          }

          .rbc-event-content {
            font-size: 0.85rem;
          }

          .rbc-show-more {
            color: #e91e63;
            font-weight: 600;
            background-color: transparent;
            padding: 4px;
            border-radius: 4px;
          }

          .rbc-show-more:hover {
            background-color: rgba(233, 30, 99, 0.1);
          }
        `}</style>
      </Paper>

      {/* Dialog for showing all dreams on a day */}
      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            bgcolor: 'background.paper',
            backgroundImage: 'none',
            maxHeight: '80vh',
          },
        }}
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h6">Dreams</Typography>
            {selectedDate && (
              <Typography variant="caption" color="text.secondary">
                {format(selectedDate, 'EEEE, MMMM d, yyyy')}
              </Typography>
            )}
          </Box>
          <IconButton onClick={handleCloseDialog} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ overflow: 'auto', p: 2 }}>
          {selectedDateDreams.map((dream, idx) => {
            const messages = dream.messages || [];

            return (
              <Accordion
                key={dream.id}
                sx={{
                  mb: 1,
                  bgcolor: 'background.paper',
                  '&:before': { display: 'none' },
                }}
              >
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  sx={{
                    '&:hover': {
                      bgcolor: 'action.hover',
                    },
                  }}
                >
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                      {dream.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {dream.preview}
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails sx={{ pt: 0 }}>
                  {messages.length > 0 ? (
                    <Box>
                      {messages.map((msg, msgIdx) => (
                        <Box key={msg.id}>
                          <Box
                            sx={{
                              p: 2,
                              bgcolor: msg.role === 'user' ? 'rgba(233, 30, 99, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                              borderLeft: 3,
                              borderColor: msg.role === 'user' ? '#e91e63' : 'rgba(255, 255, 255, 0.2)',
                            }}
                          >
                            <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 1, textTransform: 'uppercase', color: msg.role === 'user' ? '#e91e63' : 'text.secondary' }}>
                              {msg.role === 'user' ? 'You' : 'AI'}
                            </Typography>
                            <Box
                              sx={{
                                fontSize: '0.875rem',
                                '& p': { mb: 1 },
                                '& ul, & ol': { pl: 2, mb: 1 },
                                '& li': { mb: 0.5 },
                                '& h1, & h2, & h3, & h4, & h5, & h6': { mt: 1.5, mb: 1, fontWeight: 'bold' },
                                '& code': {
                                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                                  px: 0.5,
                                  py: 0.25,
                                  borderRadius: 0.5,
                                  fontSize: '0.85em',
                                  fontFamily: 'monospace',
                                },
                                '& pre': {
                                  bgcolor: 'rgba(0, 0, 0, 0.3)',
                                  p: 1.5,
                                  borderRadius: 1,
                                  overflow: 'auto',
                                  '& code': {
                                    bgcolor: 'transparent',
                                    p: 0,
                                  },
                                },
                                '& strong': { fontWeight: 'bold' },
                                '& em': { fontStyle: 'italic' },
                                '& blockquote': {
                                  borderLeft: 3,
                                  borderColor: 'rgba(255, 255, 255, 0.2)',
                                  pl: 2,
                                  ml: 0,
                                  fontStyle: 'italic',
                                },
                              }}
                            >
                              <ReactMarkdown>{msg.content}</ReactMarkdown>
                            </Box>
                          </Box>
                          {msgIdx < messages.length - 1 && <Divider sx={{ my: 1 }} />}
                        </Box>
                      ))}
                    </Box>
                  ) : (
                    <Typography variant="caption" color="text.secondary">No messages</Typography>
                  )}
                </AccordionDetails>
              </Accordion>
            );
          })}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default DreamCalendar;
