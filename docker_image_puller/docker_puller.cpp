#include <iostream>
#include <vector>
#include <fstream>
#include <string>

#include <ctime>
#include <unistd.h>
#include <sys/wait.h>

using namespace std;

int main()
{
	time_t current_timer;
	struct tm* t;

	string resource_path = 

	vector <string> my_cms = {"wordpress", "joomla", "drupal", "october-dev", "pagekit", "prestashop", "qloapps_docker"};

	int image_count = 0;

	for(int i = 0 ; i < my_cms.size() ; i++)
	{

		int current_count = 0;

		cout << "⚙️ Download CMS: " << my_cms[i] << endl;

		string version_folder = "../docker_hub_library_version/";
		string file_path = version_folder + my_cms[i] + "_version";

		// Version Info File Open
		ifstream version_info;
		cout << "Open file from " << file_path << endl;
		version_info.open(file_path);
		
		// Fail to open file
		if(!version_info)
		{
			cerr << "❌ Fail to open file..." << endl << endl;
			continue;
		}
		// Success to open file
		cout << "✅ Successfully open file!" << endl;

		char version_num[256] = {0, };
		while(version_info.getline(version_num, 256))
		{
			cout << 80 - image_count%80 << " images left before sleep!" << endl;

			// Waiting for docker. 80 images with 2 hours
			if(image_count != 0 && image_count % 80 == 0)
			{
				current_timer = time(NULL);
				t = localtime(&current_timer);

				cout << "⏳ 80 images downloaded time: " << t->tm_mon + 1 << ". " << t->tm_mday << ". " << t->tm_hour << ":" << t->tm_min << endl;
				cout << "Next starting time: " << t->tm_hour + 2 << ":" << t->tm_min << endl;
				cout << "💤 Waiting for 2 Hours..." << endl;

				sleep(7200);

				cout << "🚀 Now restart!!!" << endl;
			}

			cout << "🐳 Start pulling docker with version " << version_num << "..." << endl;

			// check cms name
			string cms_name_ver;
			if(my_cms[i] == "wp")
				cms_name_ver = "wordpress:" + (string)version_num;
			else
				cms_name_ver = my_cms[i] + ":" + version_num;


			// make child processor
			pid_t pid = fork();

			if(pid == 0)
			{
				char *args[] = {
					(char *) "docker",
					(char *) "pull",
					(char *) cms_name_ver.c_str(),
					NULL
				};
				execvp("docker", args);
				perror("❌ Failed to pulling image...");
				return 1;
			}
			else if(pid > 0)
			{
				int status;
				waitpid(pid, &status, 0);
				image_count++;
				current_count++;
			}
			else
			{
				perror("❌ Fork failed...");
			}

			
		}

		// Notice Current Successed
		cout << "🎉 Total " << current_count << " images pulled!" << endl;

		// File Closing
		cout << " ...END! File closing" << endl;
		version_info.close();

		cout << endl;
	}

	return 0;
}
