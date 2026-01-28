import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";
import Pets from "./pages/Pets";
import PetProfile from "./pages/PetProfile";
import HealthRecords from "./pages/HealthRecords";
import Vaccinations from "./pages/Vaccinations";
import BehaviorLogs from "./pages/BehaviorLogs";
import WeightTracking from "./pages/WeightTracking";
import Expenses from "./pages/Expenses";
import FeedingSchedule from "./pages/FeedingSchedule";
import SickCare from "./pages/SickCare";
import Subscription from "./pages/Subscription";
import LandingPage from "./pages/LandingPage";

import Medications from "./pages/Medications";
import DailyActivities from "./pages/DailyActivities";

function Router() {
  return (
    <Switch>
      <Route path={"/"} component={Home} />
      <Route path={"/pets"} component={Pets} />
      <Route path={"/health-records"} component={HealthRecords} />
      <Route path={"/vaccinations"} component={Vaccinations} />
      <Route path={"/behavior-logs"} component={BehaviorLogs} />
      <Route path={"/weight-tracking"} component={WeightTracking} />
      <Route path={"/feeding-schedule"} component={FeedingSchedule} />
      <Route path={"/expenses"} component={Expenses} />
      <Route path={"/sick-care"} component={SickCare} />
      <Route path={"/medications"} component={Medications} />
      <Route path={"/daily-activities"} component={DailyActivities} />
      <Route path={"/pets/:id"} component={PetProfile} />
      <Route path={"/subscription"} component={Subscription} />
      <Route path={"/landing"} component={LandingPage} />
      <Route path={"/404"} component={NotFound} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
