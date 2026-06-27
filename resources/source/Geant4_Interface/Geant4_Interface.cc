#include <CLI/CLI.hpp>
#include "G4RunManagerFactory.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "G4UIExecutive.hh"
#include "G4VUserDetectorConstruction.hh"
#include "G4GDMLParser.hh"
#include "ActionInitialization.hh"
#include "FTFP_BERT.hh"

class GDMLDetectorConstruction : public G4VUserDetectorConstruction
{
  private:
    G4VPhysicalVolume* fWorldVolume;
  public:
    GDMLDetectorConstruction(G4VPhysicalVolume* world) : fWorldVolume(world) {}
    ~GDMLDetectorConstruction() override {}
    G4VPhysicalVolume* Construct() override { return fWorldVolume; }
};

int main(int argc, char** argv)
{

  // 1. Define default argument values
  std::string initfile_name = "";
  std::string geometryfile_name = "";
  std::string outputfile_name = "";
  bool use_ui = false;
  bool use_gps = false;

  // 2. Set up the parser
  CLI::App app{"Geant4 Simulation Application"};
  app.add_option("geometry", geometryfile_name, "GDML geometry file")
   ->required();
  app.add_option("-m,--macro", initfile_name, "Macro to execute on start");
  app.add_option("-o,--output", outputfile_name, "Output file for histogram");
  app.add_flag("-i,--interactive", use_ui, "Use interactive user interface");
  app.add_flag("-g,--gps", use_gps, "Use general particle source");

  // 3. Parse arguments
  try {
      app.parse(argc, argv);
  } catch (const CLI::ParseError &e) {
      return app.exit(e);
  }


  G4UIExecutive* ui = nullptr;
  if ( use_ui ) {
    ui = new G4UIExecutive(argc, argv);
  }

  auto* runManager = G4RunManagerFactory::CreateRunManager(G4RunManagerType::Default);

  G4GDMLParser parser;
  parser.Read(geometryfile_name, false);
  G4VPhysicalVolume* worldVolume = parser.GetWorldVolume();

  // Find all logical volumes with custom tag
  std::map<G4String, std::set<G4LogicalVolume*>> sensitiveVolumes;
  const G4GDMLAuxMapType* auxMap = parser.GetAuxMap();

  if (auxMap) {
    for (auto const& [logVol, auxList] : *auxMap) {
      for (auto const& auxInfo : auxList) {
        if (auxInfo.type == "SensDet") {
          G4cout << "--> C++ Init: Registered sensitive volume: " << logVol->GetName() << G4endl;
          if (sensitiveVolumes.count(auxInfo.value) == 0) {
              sensitiveVolumes[auxInfo.value] = {};
          }
          sensitiveVolumes[auxInfo.value].insert(logVol);
        }
      }
    }
  }


  runManager->SetUserInitialization(new GDMLDetectorConstruction(worldVolume));
  runManager->SetUserInitialization(new FTFP_BERT);
  runManager->SetUserInitialization(new ActionInitialization(use_gps, sensitiveVolumes, outputfile_name));

  G4VisManager* visManager = new G4VisExecutive;
  visManager->Initialize();

  G4UImanager* UImanager = G4UImanager::GetUIpointer();

  if ( initfile_name != "" ) {
    G4String command = "/control/execute ";
    UImanager->ApplyCommand(command+initfile_name);
  }

  if ( use_ui ) {
    ui->SessionStart();
    delete ui;
  }

  delete visManager;
  delete runManager;
  return 0;
}
