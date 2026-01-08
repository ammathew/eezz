import UserProfile from "./views/UserProfile";
import AdStudio from "./views/AdStudio";

// MUI Icons
import PersonIcon from '@mui/icons-material/Person';
import CampaignIcon from '@mui/icons-material/Campaign';

const routes = [
  {
    path: "/ad-studio",
    name: "Ad Studio",
    icon: <CampaignIcon />,
    component: <AdStudio />,
  },
  {
    path: "/profile",
    name: "User Profile",
    icon: <PersonIcon />,
    component: <UserProfile />,
  },
];

export default routes;
