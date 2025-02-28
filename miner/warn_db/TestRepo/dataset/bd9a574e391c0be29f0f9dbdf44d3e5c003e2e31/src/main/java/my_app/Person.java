package my_app;

public class Person{
	public static int WORKING_HOURS = 8;
    private String[] hobbies;
    protected Date birthDate;
    
    public Person(){
		hobbies = new String[]{};
		birthDate = new Date();
	}
	
    public Date getBirthDate()
    {return(birthDate);}
    
    public void setBirthDate(final Date birthDate)
    {this.birthDate = birthDate;}
	
    String[] getHobbies(){ return hobbies;}
	
    void setHobbies(String[] hobbies){ this.hobbies = hobbies;}
}

class Date{
	int year, month, day;
	
    public Date() {
        year = 1010;
        month = 10;
        day = 10;
    }
	
	@Override
    public String toString() {
        return this.year + "." + this.month + "." + this.day + ".";
    }
}

