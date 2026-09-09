import express from 'express';
import session from 'express-session';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { config } from './config.js';
import authRoutes from './routes/auth.js';
import apiRoutes from './routes/api.js';
import { startScheduler } from './scheduler.js';
import './db.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const app = express();

app.use(
  session({
    secret: config.sessionSecret,
    resave: false,
    saveUninitialized: false,
    cookie: { httpOnly: true, sameSite: 'lax' },
  }),
);
app.use(express.json());

app.use('/auth', authRoutes);
app.use('/api', apiRoutes);
app.use(express.static(path.join(__dirname, '..', 'public')));

app.listen(config.port, () => {
  console.log(`Desk-R Social Analytics laeuft auf ${config.baseUrl}`);
  startScheduler();
});
